import logging
import os
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

TUTOR_SYSTEM_PROMPT = """You are a Socratic clinical reasoning tutor for Indian medical students (MBBS final year, interns, NEET-PG aspirants).

Your role:
- Guide the student through clinical reasoning using the Socratic method
- Ask probing questions instead of giving answers directly
- Expose cognitive biases (anchoring, premature closure, availability, confirmation)
- Encourage systematic differential diagnosis
- Keep responses concise (2-4 sentences max)
- Reference the Indian clinical context when relevant

Case context:
- Chief complaint: {chief_complaint}
- Specialty: {specialty}
- Difficulty: {difficulty}

IMPORTANT: Never reveal the diagnosis directly. Guide the student to discover it themselves."""


class SocraticTutor:
    """AI tutor that uses Socratic method to guide clinical reasoning."""

    def __init__(self):
        self.conversation_history: list = []
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        if self.api_key and self.api_key != "sk-ant-your-key-here":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Claude client init failed for tutor: {e}")

    def respond(self, student_message: str, case_context: dict) -> str:
        """Generate Socratic response to student's reasoning."""

        self.conversation_history.append({
            "role": "user",
            "content": student_message,
        })

        # Try Claude API first, fallback to keyword-based
        if self.client:
            response = self._respond_with_claude(student_message, case_context)
            if response:
                self.conversation_history.append({"role": "assistant", "content": response})
                return response

        response = self._keyword_fallback(student_message, case_context)
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _respond_with_claude(self, message: str, context: dict) -> Optional[str]:
        """Generate a Socratic response using Claude API."""
        system = TUTOR_SYSTEM_PROMPT.format(
            chief_complaint=context.get("chief_complaint", "unknown"),
            specialty=context.get("specialty", "general"),
            difficulty=context.get("difficulty", "intermediate"),
        )

        messages = self.conversation_history.copy()

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=300,
                system=system,
                messages=messages,
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Tutor Claude API error: {e}")
            return None

    def _keyword_fallback(self, message: str, context: dict) -> str:
        """Keyword-based fallback when Claude API is unavailable."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["heart attack", "mi", "stemi", "acs"]):
            return "You're considering an acute coronary event. That's a reasonable starting point given the presentation. But what features of this case are unusual for a typical MI? What risk factors stand out?"

        if any(word in message_lower for word in ["cocaine", "drug", "substance"]):
            return "Excellent observation about the substance use. How does cocaine specifically affect the coronary vasculature? And critically - how does this change your management compared to a standard ACS protocol?"

        if any(word in message_lower for word in ["pe", "embolism", "dvt"]):
            return "Pulmonary embolism is an important differential for chest pain. What clinical features would help you distinguish PE from ACS in this patient? What investigation would be most helpful?"

        if any(word in message_lower for word in ["beta blocker", "metoprolol", "atenolol"]):
            return "Think carefully about beta-blockers in this context. What happens physiologically when you block beta-receptors in a patient with cocaine on board? This is a critical management distinction."

        if len(self.conversation_history) <= 2:
            return "Let's think through this systematically. What are the most dangerous causes of this presentation you need to rule out first? Start with your differential diagnosis."

        return "Good thinking. Can you explain your reasoning further? What evidence supports your hypothesis, and what evidence might contradict it?"

    def reset(self):
        """Reset conversation for a new case."""
        self.conversation_history = []
