"""Patient Agent - Generates realistic patient responses using Claude Opus."""
import logging
import os
from typing import Optional

import anthropic

from app.models.simulation import EmotionalState, PatientGender

logger = logging.getLogger(__name__)


PATIENT_SYSTEM_PROMPT = """You are a {age}yo {gender} patient in {setting}. You're feeling {emotional_state}.

CRITICAL RULES:
1. NEVER use medical jargon - you're not a doctor
2. Speak naturally using simple language
3. Mix Hindi-English words naturally if appropriate (e.g., "dard hai", "seene mein")
4. Show emotion in your responses
5. Your emotional state affects how you respond:
   - CALM: Cooperative, detailed answers, trusting
   - CONCERNED: A bit worried, needs reassurance, mostly cooperative
   - ANXIOUS: Short answers, worried, needs calming down first
   - DEFENSIVE: Resistant, minimal answers, feels judged or rushed

IMPORTANT BEHAVIOR RULES:
- If student is warm/empathetic → you become more CALM
- If student is cold/rushed/dismissive → you become more DEFENSIVE/ANXIOUS
- If student asks open-ended questions → you give more details
- If student just fires closed questions → you give minimal yes/no answers
- If student acknowledges your distress → you calm down

Your complaint: {chief_complaint}

Key information you know (only share if asked properly):
{key_history}

Physical symptoms you're experiencing:
{physical_symptoms}

Examples of realistic patient speech:
- Good: "Doctor, seene mein bahut dard ho raha hai, left side mein"
- Bad: "I have substernal chest pain radiating to the left arm"

- Good: "Haan doctor, mujhe diabetes hai, 5 saal se"
- Bad: "I have type 2 diabetes mellitus for 5 years"

Respond AS THE PATIENT. Stay in character."""


class PatientAgent:
    """Simulates a realistic patient using Claude Opus API."""

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        if self.api_key and self.api_key != "sk-ant-your-key-here":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Claude client for patient agent: {e}")
                raise

    def generate_response(
        self,
        student_message: str,
        patient_profile: dict,
        emotional_state: EmotionalState,
        conversation_history: list,
    ) -> str:
        """Generate patient response based on student message and current state."""

        if not self.client:
            raise ValueError("Claude API client not initialized")

        # Build patient context
        system_prompt = PATIENT_SYSTEM_PROMPT.format(
            age=patient_profile["age"],
            gender=patient_profile["gender"],
            setting=patient_profile["setting"],
            emotional_state=emotional_state.value,
            chief_complaint=patient_profile["chief_complaint"],
            key_history="\n".join(f"- {item}" for item in patient_profile.get("key_history_points", [])),
            physical_symptoms=patient_profile.get("physical_symptoms", "Describe as appropriate"),
        )

        # Build conversation history
        messages = []
        for msg in conversation_history:
            messages.append({
                "role": "user" if msg["role"] == "student" else "assistant",
                "content": msg["content"],
            })

        # Add current student message
        messages.append({
            "role": "user",
            "content": student_message,
        })

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=400,
                system=system_prompt,
                messages=messages,
                temperature=0.8,  # Slightly higher for natural variation
            )
            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Patient agent API error: {e}")
            return self._fallback_response(emotional_state)

    def generate_initial_greeting(
        self,
        patient_profile: dict,
        emotional_state: EmotionalState,
    ) -> str:
        """Generate patient's first words when student enters."""

        if not self.client:
            return self._fallback_greeting(emotional_state)

        system_prompt = f"""You are a {patient_profile['age']}yo {patient_profile['gender']} patient in {patient_profile['setting']}.
You're feeling {emotional_state.value} and just walked in.

Generate your FIRST words to the doctor. Keep it very short (1-2 sentences).
Use natural language, NO medical jargon.
Show your emotional state."""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=150,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Patient with {patient_profile['chief_complaint']} enters. What do you say first?",
                }],
                temperature=0.8,
            )
            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Patient greeting generation error: {e}")
            return self._fallback_greeting(emotional_state)

    def _fallback_response(self, emotional_state: EmotionalState) -> str:
        """Fallback response if API fails."""
        responses = {
            EmotionalState.CALM: "Haan doctor, aap puchiye. Main bata dunga.",
            EmotionalState.CONCERNED: "Doctor, kuch samajh nahi aa raha. Sab theek ho jayega na?",
            EmotionalState.ANXIOUS: "Bahut dard ho raha hai doctor... bahut dard...",
            EmotionalState.DEFENSIVE: "Maine pehle bhi bataya. Aur kya puchna hai?",
        }
        return responses.get(emotional_state, "Haan doctor?")

    def _fallback_greeting(self, emotional_state: EmotionalState) -> str:
        """Fallback greeting if API fails."""
        greetings = {
            EmotionalState.CALM: "Namaste doctor. Main aaj theek nahi feel kar raha.",
            EmotionalState.CONCERNED: "Doctor, bahut problem ho rahi hai...",
            EmotionalState.ANXIOUS: "Doctor... doctor please help... bahut dard hai!",
            EmotionalState.DEFENSIVE: "Kya hai doctor? Bahut busy lag rahe ho.",
        }
        return greetings.get(emotional_state, "Namaste doctor.")
