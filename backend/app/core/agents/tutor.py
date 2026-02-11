import os
from typing import Optional


class SocraticTutor:
    """AI tutor that uses Socratic method to guide clinical reasoning."""

    def __init__(self):
        self.conversation_history: list = []
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")

    def respond(self, student_message: str, case_context: dict) -> str:
        """Generate Socratic response to student's reasoning."""

        # For demo, use pre-built responses
        # In production, this would call Claude API
        self.conversation_history.append({
            "role": "user",
            "content": student_message,
        })

        response = self._generate_socratic_response(student_message, case_context)

        self.conversation_history.append({
            "role": "assistant",
            "content": response,
        })

        return response

    def _generate_socratic_response(self, message: str, context: dict) -> str:
        """Generate a teaching response using Socratic method."""

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
            return "Let's think through this systematically. What are the most dangerous causes of chest pain you need to rule out first? Start with your differential diagnosis."

        return "Good thinking. Can you explain your reasoning further? What evidence supports your hypothesis, and what evidence might contradict it?"

    def reset(self):
        """Reset conversation for a new case."""
        self.conversation_history = []
