"""Clinical validator — safety gate for dangerous student actions.

Catches critical errors BEFORE they harm the virtual patient:
- Drug interactions with existing medications
- Contraindicated drugs for the patient's condition
- Missing critical steps (e.g., checking creatinine before contrast)
- Dose errors

When danger is detected, agents intervene with teaching moments —
not just blocks. This is how real hospitals work: the nurse catches
a potentially wrong order and confirms before administering.
"""

import logging
import os
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

VALIDATION_PROMPT = """You are a CLINICAL SAFETY OFFICER in an Indian teaching hospital. Your job is to check if a medical student's action could harm the patient.

PATIENT CONTEXT:
- Diagnosis: {diagnosis}
- Age/Gender: {age}y {gender}
- Chief complaint: {chief_complaint}
- Current vitals: BP {bp}, HR {hr}, RR {rr}, Temp {temp}°C, SpO2 {spo2}%
- History: {history}
- Existing treatments: {existing_treatments}

STUDENT'S ACTION: "{student_action}"
ACTION TYPE: {action_type}

CHECK FOR:
1. DANGEROUS drug interactions (with existing treatments or known conditions)
2. CONTRAINDICATED treatments (e.g., beta-blocker in acute decompensated heart failure with cardiogenic shock)
3. MISSING PREREQUISITES (e.g., ordering contrast CT without checking renal function)
4. DOSE ERRORS (if dose is specified — 10x overdose patterns are common student errors)
5. INAPPROPRIATE for the clinical scenario (e.g., discharging a critically ill patient)

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "safety_level": "safe" | "caution" | "dangerous",
    "issues": [
        {{
            "type": "contraindication" | "interaction" | "missing_step" | "dose_error" | "inappropriate",
            "description": "What the specific issue is",
            "severity": "low" | "medium" | "high" | "critical"
        }}
    ],
    "nurse_intervention": "What Nurse Priya would say to gently flag this (or null if safe)",
    "senior_intervention": "What Dr. Sharma would say if it's dangerous (or null if safe/caution)",
    "proceed": true | false,
    "teaching_point": "The clinical lesson here (for the student to learn from)"
}}

IMPORTANT:
- Most routine actions are SAFE — don't over-flag
- Investigations are almost always safe (except invasive ones without consent/preparation)
- History taking and examination are ALWAYS safe
- Only flag treatments that could genuinely harm
- In caution cases, nurse confirms but allows proceeding
- In dangerous cases, both nurse and senior intervene — this is a TEACHING moment"""


class ClinicalValidator:
    """Validates student actions for clinical safety.

    Uses Claude Opus to reason about safety in the specific clinical context,
    rather than relying on a static rules database.
    """

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client: Optional[anthropic.Anthropic] = None
        if self.api_key and self.api_key != "sk-ant-your-key-here":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"ClinicalValidator init failed: {e}")

    def validate_action(
        self,
        student_action: str,
        action_type: str,
        case_data: dict,
        current_vitals: dict,
        existing_treatments: list[dict],
    ) -> dict:
        """Validate a student action for clinical safety.

        Args:
            student_action: What the student wants to do
            action_type: Category (order_treatment, order_investigation, etc.)
            case_data: Full case data
            current_vitals: Current vital signs
            existing_treatments: Previously ordered treatments

        Returns:
            Validation result with safety_level, issues, and agent interventions.
        """
        # History taking, examination, and conversations are always safe
        safe_actions = {"talk_to_patient", "ask_nurse", "consult_senior", "examine_patient", "team_huddle"}
        if action_type in safe_actions:
            return {
                "safety_level": "safe",
                "issues": [],
                "nurse_intervention": None,
                "senior_intervention": None,
                "proceed": True,
                "teaching_point": None,
            }

        if not self.client:
            return self._fallback_validation(student_action, action_type)

        vitals = current_vitals
        history = ""
        for stage in case_data.get("stages", []):
            if stage.get("stage") == "history":
                history = stage.get("info", "")[:500]
                break

        prompt = VALIDATION_PROMPT.format(
            diagnosis=case_data.get("diagnosis", "Under evaluation"),
            age=case_data.get("patient", {}).get("age", "Unknown"),
            gender=case_data.get("patient", {}).get("gender", "Unknown"),
            chief_complaint=case_data.get("chief_complaint", ""),
            bp=f"{vitals.get('bp_systolic', 120)}/{vitals.get('bp_diastolic', 80)}",
            hr=vitals.get("hr", 80),
            rr=vitals.get("rr", 16),
            temp=vitals.get("temp", 37.0),
            spo2=vitals.get("spo2", 98),
            history=history,
            existing_treatments="; ".join(tx.get("description", "") for tx in existing_treatments) or "None",
            student_action=student_action,
            action_type=action_type,
        )

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1500,
                temperature=1,
                thinking={
                    "type": "enabled",
                    "budget_tokens": 4000,
                },
                messages=[{"role": "user", "content": prompt}],
            )

            content = ""
            for block in response.content:
                if block.type == "text":
                    content = block.text.strip()

            if content:
                return self._parse_validation(content)

        except Exception as e:
            logger.error(f"ClinicalValidator error: {e}")

        return self._fallback_validation(student_action, action_type)

    def _parse_validation(self, response_text: str) -> dict:
        """Parse Claude's JSON validation response."""
        import json

        try:
            text = response_text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            result = json.loads(text.strip())

            return {
                "safety_level": result.get("safety_level", "safe"),
                "issues": result.get("issues", []),
                "nurse_intervention": result.get("nurse_intervention"),
                "senior_intervention": result.get("senior_intervention"),
                "proceed": result.get("proceed", True),
                "teaching_point": result.get("teaching_point"),
            }
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.warning(f"Failed to parse validation JSON: {e}")
            return self._fallback_validation("", "")

    def _fallback_validation(self, student_action: str, action_type: str) -> dict:
        """Conservative fallback — allow with caution for treatments."""
        if action_type == "order_treatment":
            return {
                "safety_level": "caution",
                "issues": [],
                "nurse_intervention": f"Doctor, just confirming the order — {student_action}. Shall I proceed?",
                "senior_intervention": None,
                "proceed": True,
                "teaching_point": None,
            }

        return {
            "safety_level": "safe",
            "issues": [],
            "nurse_intervention": None,
            "senior_intervention": None,
            "proceed": True,
            "teaching_point": None,
        }


# Singleton
clinical_validator = ClinicalValidator()
