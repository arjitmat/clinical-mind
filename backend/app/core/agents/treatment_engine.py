"""Treatment engine — models drug effects, contraindications, and patient outcomes.

Uses Claude Opus to dynamically assess treatment appropriateness and predict effects.
No hardcoded drug databases — the AI reasons about each treatment in context.
"""

import logging
import os
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

# Treatment categories and their typical vitals effects (used as guidance for Claude)
TREATMENT_GUIDANCE = """
TREATMENT ASSESSMENT FRAMEWORK:

You are a clinical pharmacologist assessing a treatment order in an Indian government hospital.

AVAILABLE RESOURCES (Indian Govt Hospital):
- NLEM drugs (National List of Essential Medicines) are available
- Non-NLEM drugs: may need special indent, delay
- IV fluids: NS 0.9%, RL, DNS (Dextrose Normal Saline), D5W, D10W
- Blood products: available after crossmatch (30-60 min)
- Emergency drugs: Adrenaline, Atropine, Dopamine, Dobutamine, Furosemide, Hydrocortisone
- Antibiotics: Commonly available — Amoxicillin, Ceftriaxone, Metronidazole, Azithromycin, Ciprofloxacin, Doxycycline, Gentamicin
- Analgesics: Paracetamol, Diclofenac, Tramadol; Morphine (needs controlled drug register)
- Antihypertensives: Amlodipine, Atenolol, Enalapril, Losartan, Nifedipine
- Antidiabetics: Metformin, Glimepiride, Insulin (Regular, NPH)
- Anticoagulants: Heparin, Warfarin, Enoxaparin
- Bronchodilators: Salbutamol nebulization, Ipratropium, Aminophylline
- Steroids: Prednisolone, Hydrocortisone, Dexamethasone, Methylprednisolone
- Antimalarials: Artesunate, ACT, Chloroquine, Primaquine

ASSESSMENT CRITERIA:
1. Is this treatment APPROPRIATE for the patient's condition?
2. Are there CONTRAINDICATIONS based on the patient's history/vitals?
3. Is the DOSE reasonable (if specified)?
4. Is the drug AVAILABLE in a govt hospital?
5. What VITAL SIGN EFFECTS would this treatment have?

RESPOND IN THIS EXACT JSON FORMAT:
{
    "is_appropriate": true/false,
    "safety_level": "safe" | "caution" | "dangerous",
    "reasoning": "Brief clinical reasoning for the assessment",
    "availability": "available" | "special_indent" | "referral_needed",
    "vital_effects": {
        "hr_change": 0,
        "bp_systolic_change": 0,
        "spo2_change": 0,
        "rr_change": 0,
        "temp_change": 0.0
    },
    "nurse_response": "What the nurse would say when given this order",
    "monitoring": "What to monitor after this treatment",
    "alternative": "If inappropriate, suggest what should be given instead (or null)"
}

IMPORTANT:
- vital_effects values are CHANGES (positive = increase, negative = decrease)
- Be realistic — IV fluids raise BP by 10-15mmHg, not 50
- Antipyretics reduce temp by 0.5-1.0°C, not instantly normalize
- O2 supplementation raises SpO2 by 3-8% depending on delivery method
- Beta blockers reduce HR by 10-20 bpm
- If treatment is dangerous, still estimate effects but flag the danger
"""


class TreatmentEngine:
    """Assesses and models treatment effects using Claude Opus.

    This is NOT a static drug database — it uses Claude's medical knowledge
    to reason about each treatment in the specific clinical context.
    """

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client: Optional[anthropic.Anthropic] = None
        if self.api_key and self.api_key != "sk-ant-your-key-here":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"TreatmentEngine Claude init failed: {e}")

    def assess_treatment(
        self,
        treatment_description: str,
        case_data: dict,
        current_vitals: dict,
        existing_treatments: list[dict],
        specialized_knowledge: str = "",
    ) -> dict:
        """Assess a treatment order for appropriateness and predict effects.

        Args:
            treatment_description: What the student ordered (e.g., "Start IV NS 1L stat")
            case_data: Full case data dict
            current_vitals: Current vital signs
            existing_treatments: Previously ordered treatments
            specialized_knowledge: Agent's dynamic knowledge for this case

        Returns:
            Assessment dict with safety_level, vital_effects, nurse_response, etc.
        """
        if not self.client:
            return self._fallback_assessment(treatment_description, current_vitals)

        # Build the assessment prompt
        vitals = current_vitals
        prompt = f"""{TREATMENT_GUIDANCE}

PATIENT CONTEXT:
- Diagnosis: {case_data.get('diagnosis', 'Under evaluation')}
- Age/Gender: {case_data.get('patient', {}).get('age', 'Unknown')}y {case_data.get('patient', {}).get('gender', 'Unknown')}
- Chief complaint: {case_data.get('chief_complaint', '')}
- Current vitals: BP {vitals.get('bp_systolic', 120)}/{vitals.get('bp_diastolic', 80)}, HR {vitals.get('hr', 80)}, RR {vitals.get('rr', 16)}, Temp {vitals.get('temp', 37.0)}°C, SpO2 {vitals.get('spo2', 98)}%
- Existing treatments: {'; '.join(tx.get('description', '') for tx in existing_treatments) or 'None yet'}
- Difficulty: {case_data.get('difficulty', 'intermediate')}

CASE-SPECIFIC KNOWLEDGE:
{specialized_knowledge[:2000] if specialized_knowledge else 'No additional context available.'}

STUDENT'S TREATMENT ORDER:
"{treatment_description}"

Assess this treatment order. Respond ONLY with the JSON object."""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2000,
                temperature=1,
                thinking={
                    "type": "adaptive",
                },
                messages=[{"role": "user", "content": prompt}],
            )

            content = ""
            for block in response.content:
                if block.type == "text":
                    content = block.text.strip()

            if content:
                return self._parse_assessment(content, treatment_description)

        except Exception as e:
            logger.error(f"TreatmentEngine assessment error: {e}")

        return self._fallback_assessment(treatment_description, current_vitals)

    def _parse_assessment(self, response_text: str, treatment_description: str) -> dict:
        """Parse Claude's JSON response into a structured assessment."""
        import json

        # Try to extract JSON from the response
        try:
            # Handle case where response has markdown code blocks
            text = response_text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            result = json.loads(text.strip())

            # Ensure required fields
            return {
                "is_appropriate": result.get("is_appropriate", True),
                "safety_level": result.get("safety_level", "safe"),
                "reasoning": result.get("reasoning", "Assessment completed."),
                "availability": result.get("availability", "available"),
                "vital_effects": result.get("vital_effects", {}),
                "nurse_response": result.get("nurse_response", f"Noted, doctor. Starting {treatment_description}."),
                "monitoring": result.get("monitoring", "Continue routine monitoring."),
                "alternative": result.get("alternative"),
                "treatment_description": treatment_description,
            }
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.warning(f"Failed to parse treatment assessment JSON: {e}")
            return self._fallback_assessment(treatment_description, {})

    def _fallback_assessment(self, treatment_description: str, current_vitals: dict) -> dict:
        """Fallback when Claude is unavailable — conservative assessment."""
        desc_lower = treatment_description.lower()

        # Basic pattern matching for common treatments
        effects = {}
        safety = "safe"
        nurse_msg = f"Noted, doctor. Starting {treatment_description}."

        if any(w in desc_lower for w in ["iv fluid", "ns ", "normal saline", "rl ", "ringer"]):
            effects = {"bp_systolic_change": 10, "hr_change": -5}
            nurse_msg = "Starting IV fluids as ordered. I'll monitor the drip rate."

        elif any(w in desc_lower for w in ["oxygen", "o2", "nasal cannula", "mask"]):
            effects = {"spo2_change": 5, "rr_change": -2}
            nurse_msg = "Starting O2 supplementation. I'll monitor SpO2 closely."

        elif any(w in desc_lower for w in ["paracetamol", "pcm", "antipyretic"]):
            effects = {"temp_change": -0.5}
            nurse_msg = "Giving paracetamol as ordered. I'll recheck temperature in 30 minutes."

        elif any(w in desc_lower for w in ["nebulization", "nebuliser", "salbutamol"]):
            effects = {"spo2_change": 3, "rr_change": -3, "hr_change": 5}
            nurse_msg = "Setting up nebulization now. I'll monitor the patient during the procedure."

        elif any(w in desc_lower for w in ["antibiotic", "ceftriaxone", "amoxicillin"]):
            effects = {}  # Antibiotics don't have immediate vital effects
            nurse_msg = "Noted. I'll prepare the antibiotic and do a test dose first as per protocol."

        else:
            safety = "caution"
            nurse_msg = f"Doctor, just confirming — you want to start {treatment_description}? I'll prepare it right away."

        return {
            "is_appropriate": True,
            "safety_level": safety,
            "reasoning": "Assessment based on standard protocols (Claude API unavailable for detailed assessment).",
            "availability": "available",
            "vital_effects": effects,
            "nurse_response": nurse_msg,
            "monitoring": "Continue monitoring vitals post-treatment.",
            "alternative": None,
            "treatment_description": treatment_description,
        }


# Singleton
treatment_engine = TreatmentEngine()
