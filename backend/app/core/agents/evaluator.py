"""Evaluator Agent - Analyzes student communication and updates patient state."""
import logging
import os
from typing import Dict, Tuple

import anthropic

from app.models.simulation import EmotionalState, RapportLevel, FeedbackType, TutorFeedback

logger = logging.getLogger(__name__)


EVALUATOR_SYSTEM_PROMPT = """You are an expert evaluator analyzing medical student communication with patients.

Analyze the student's message for:
1. EMPATHY: Did they acknowledge patient's distress/emotions?
2. COMMUNICATION QUALITY: Open-ended questions vs closed yes/no questions?
3. BEDSIDE MANNER: Tone, warmth, professionalism
4. CLINICAL REASONING: Systematic approach vs random questioning

Based on analysis, determine:
- NEW EMOTIONAL STATE: How does the patient feel after this message?
  - If student is warm/empathetic → patient becomes more CALM
  - If student is cold/rushed → patient becomes ANXIOUS/DEFENSIVE
  - If student interrupts or dismisses → patient becomes DEFENSIVE

- RAPPORT CHANGE: Did rapport increase or decrease? (1-5 scale)
  - Open-ended questions, empathy → rapport increases
  - Closed questions, dismissive tone → rapport decreases

Current patient state:
- Emotional state: {current_emotional_state}
- Rapport level: {current_rapport}

Student message: {student_message}

Respond in this EXACT format:
NEW_EMOTIONAL_STATE: [calm/concerned/anxious/defensive]
NEW_RAPPORT: [1-5]
EMPATHY_DETECTED: [yes/no]
OPEN_ENDED_QUESTION: [yes/no]
FEEDBACK_TYPE: [positive/warning/critical]
FEEDBACK_MESSAGE: [One sentence explaining what student did well or should improve]
"""


class EvaluatorAgent:
    """Evaluates student communication and updates simulation state."""

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        if self.api_key and self.api_key != "sk-ant-your-key-here":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Claude client for evaluator: {e}")
                raise

    def evaluate_message(
        self,
        student_message: str,
        current_emotional_state: EmotionalState,
        current_rapport: RapportLevel,
    ) -> Tuple[EmotionalState, RapportLevel, TutorFeedback]:
        """
        Evaluate student message and return updated state + feedback.

        Returns:
            (new_emotional_state, new_rapport_level, feedback)
        """

        if not self.client:
            return self._fallback_evaluation(
                student_message, current_emotional_state, current_rapport
            )

        system_prompt = EVALUATOR_SYSTEM_PROMPT.format(
            current_emotional_state=current_emotional_state.value,
            current_rapport=current_rapport.value,
            student_message=student_message,
        )

        try:
            response = self.client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=300,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": "Evaluate this student message.",
                }],
                temperature=0.3,  # Lower temp for consistent evaluations
            )

            evaluation_text = response.content[0].text.strip()
            return self._parse_evaluation(evaluation_text, current_emotional_state, current_rapport)

        except Exception as e:
            logger.error(f"Evaluator API error: {e}")
            return self._fallback_evaluation(
                student_message, current_emotional_state, current_rapport
            )

    def _parse_evaluation(
        self,
        evaluation_text: str,
        current_emotional_state: EmotionalState,
        current_rapport: RapportLevel,
    ) -> Tuple[EmotionalState, RapportLevel, TutorFeedback]:
        """Parse Claude's evaluation response."""

        lines = evaluation_text.split("\n")
        parsed = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                parsed[key.strip()] = value.strip()

        # Extract values
        try:
            emotional_state_str = parsed.get("NEW_EMOTIONAL_STATE", current_emotional_state.value)
            new_emotional_state = EmotionalState(emotional_state_str.lower())
        except ValueError:
            new_emotional_state = current_emotional_state

        try:
            rapport_str = parsed.get("NEW_RAPPORT", str(current_rapport.value))
            new_rapport = RapportLevel(int(rapport_str))
        except (ValueError, KeyError):
            new_rapport = current_rapport

        try:
            feedback_type_str = parsed.get("FEEDBACK_TYPE", "warning")
            feedback_type = FeedbackType(feedback_type_str.lower())
        except ValueError:
            feedback_type = FeedbackType.WARNING

        feedback_message = parsed.get("FEEDBACK_MESSAGE", "Continue with your assessment.")

        feedback = TutorFeedback(
            type=feedback_type,
            message=feedback_message,
        )

        return new_emotional_state, new_rapport, feedback

    def _fallback_evaluation(
        self,
        student_message: str,
        current_emotional_state: EmotionalState,
        current_rapport: RapportLevel,
    ) -> Tuple[EmotionalState, RapportLevel, TutorFeedback]:
        """Simple keyword-based fallback evaluation."""

        message_lower = student_message.lower()
        new_emotional_state = current_emotional_state
        new_rapport = current_rapport

        # Detect empathy markers
        empathy_markers = ["understand", "worried", "difficult", "sorry", "must be"]
        has_empathy = any(marker in message_lower for marker in empathy_markers)

        # Detect open-ended questions
        open_ended_markers = ["tell me", "describe", "how do you", "what happened", "when did"]
        has_open_ended = any(marker in message_lower for marker in open_ended_markers)

        # Detect negative markers
        negative_markers = ["quickly", "just tell me", "yes or no", "hurry"]
        has_negative = any(marker in message_lower for marker in negative_markers)

        # Update emotional state
        if has_empathy and has_open_ended:
            # Student is doing well → patient calms down
            if current_emotional_state == EmotionalState.ANXIOUS:
                new_emotional_state = EmotionalState.CONCERNED
            elif current_emotional_state == EmotionalState.DEFENSIVE:
                new_emotional_state = EmotionalState.CONCERNED
            elif current_emotional_state == EmotionalState.CONCERNED:
                new_emotional_state = EmotionalState.CALM

            # Rapport increases
            if current_rapport.value < 5:
                new_rapport = RapportLevel(current_rapport.value + 1)

            feedback = TutorFeedback(
                type=FeedbackType.POSITIVE,
                message="Good use of open-ended questions and empathy.",
            )

        elif has_negative:
            # Student is rushed → patient becomes defensive
            if current_emotional_state == EmotionalState.CALM:
                new_emotional_state = EmotionalState.CONCERNED
            else:
                new_emotional_state = EmotionalState.DEFENSIVE

            # Rapport decreases
            if current_rapport.value > 1:
                new_rapport = RapportLevel(current_rapport.value - 1)

            feedback = TutorFeedback(
                type=FeedbackType.CRITICAL,
                message="Patient seems rushed. Try slowing down and showing empathy.",
            )

        else:
            # Neutral interaction
            feedback = TutorFeedback(
                type=FeedbackType.WARNING,
                message="Consider using more open-ended questions to build rapport.",
            )

        return new_emotional_state, new_rapport, feedback
