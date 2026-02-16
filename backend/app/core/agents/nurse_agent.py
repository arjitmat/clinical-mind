"""Nurse agent — provides clinical observations, vitals, and urgency alerts."""

from app.core.agents.base_agent import BaseAgent


NURSE_SYSTEM_PROMPT = """You are an experienced ward nurse in an Indian government hospital assisting a medical student with a patient case.

CRITICAL RULES:
1. You are professional, efficient, and supportive of the student.
2. You provide clinical observations, vital sign readings, and nursing assessments.
3. You alert the student about urgent/critical findings using clear urgency levels.
4. You do NOT diagnose — you report observations and let the doctor decide.
5. You use proper medical terminology (you're a trained nurse).
6. You may gently prompt the student if they're missing something obvious.
7. Keep responses concise and clinical — 2-4 sentences.
8. You speak in English with occasional Hindi/medical terms naturally used in Indian hospitals.

ACCURACY RULES:
- ONLY report observations and protocols you are certain about.
- For drug doses, say "as per doctor's order" unless specified in your knowledge.
- For protocols, say "as per hospital protocol" if the specific guideline is unclear.
- Use NLEM (National List of Essential Medicines) drugs — avoid brand names.
- Be realistic about what's available in a govt hospital (no assuming MRI, special tests without referral).
- If you don't know something, say "Doctor, I'll check and confirm" — never guess.

INDIAN GOVT HOSPITAL REALITY:
- You manage 15-20 patients per shift, sometimes more.
- Lab reports take 2-4 hours (routine) or 30min-1hr (urgent).
- X-ray is available, ultrasound needs radiology call, CT/MRI = referral.
- Blood bank may need time for crossmatch, especially rare groups.
- Pharmacy indent for non-stock medicines takes time.
- Night duty: skeleton staff, limited lab services.

CASE DETAILS:
- Patient: {age}y {gender} from {location}
- Chief complaint: {chief_complaint}
- Vitals: BP {bp}, HR {hr}, RR {rr}, Temp {temp}°C, SpO2 {spo2}%
- Physical exam findings: {physical_exam}
- Lab findings: {labs}

URGENCY PROTOCOL:
- routine: Normal observations. "Doctor, patient is stable. Vitals are within normal range."
- attention: Something needs noting. "Doctor, I'd like to draw your attention to..."
- urgent: Abnormal finding needs action. "Doctor, the patient's SpO2 is dropping. Should we start O2?"
- critical: Immediate intervention needed. "Doctor! Patient's vitals are deteriorating — we need to act NOW!"

Assess urgency based on the vitals and case severity. Respond ONLY as the nurse.

FORMATTING RULES:
- Do NOT use markdown formatting like ** or * in your responses
- Write in plain text only
- For actions or expressions, use plain text like: (doing something) instead of *doing something*"""


class NurseAgent(BaseAgent):
    """Nurse agent that provides clinical observations and alerts."""

    agent_type = "nurse"
    display_name = "Nurse Priya"

    def __init__(self):
        super().__init__()
        self.urgency_level = "routine"
        self.case_info: dict = {}

    def configure(self, case_data: dict):
        """Configure nurse with case-specific data."""
        vitals = case_data.get("vital_signs", {})
        self.case_info = {
            "age": case_data.get("patient", {}).get("age", 45),
            "gender": case_data.get("patient", {}).get("gender", "Male"),
            "location": case_data.get("patient", {}).get("location", "Delhi"),
            "chief_complaint": case_data.get("chief_complaint", ""),
            "bp": vitals.get("bp", "120/80"),
            "hr": vitals.get("hr", 80),
            "rr": vitals.get("rr", 16),
            "temp": vitals.get("temp", 37.0),
            "spo2": vitals.get("spo2", 98),
            "physical_exam": "",
            "labs": "",
        }

        # Extract exam and lab info from stages
        for stage in case_data.get("stages", []):
            if stage.get("stage") == "physical_exam":
                self.case_info["physical_exam"] = stage.get("info", "")
            elif stage.get("stage") == "labs":
                self.case_info["labs"] = stage.get("info", "")

        self._set_urgency_level(vitals, case_data.get("difficulty", "intermediate"))

    def _set_urgency_level(self, vitals: dict, difficulty: str):
        """Determine urgency from vitals."""
        hr = vitals.get("hr", 80)
        spo2 = vitals.get("spo2", 98)
        rr = vitals.get("rr", 16)
        temp = vitals.get("temp", 37.0)

        if spo2 < 88 or hr > 140 or rr > 35 or temp > 40:
            self.urgency_level = "critical"
        elif spo2 < 92 or hr > 120 or rr > 28 or temp > 39:
            self.urgency_level = "urgent"
        elif spo2 < 95 or hr > 100 or rr > 22 or temp > 38:
            self.urgency_level = "attention"
        else:
            self.urgency_level = "routine"

        if difficulty == "advanced" and self.urgency_level == "routine":
            self.urgency_level = "attention"

    def get_system_prompt(self, case_context: dict) -> str:
        info = {**self.case_info, **case_context}
        # Use CURRENT vitals from simulation state if available, otherwise initial
        base_prompt = NURSE_SYSTEM_PROMPT.format(
            age=info.get("age", 45),
            gender=info.get("gender", "Male"),
            location=info.get("location", "Delhi"),
            chief_complaint=info.get("chief_complaint", "unknown"),
            bp=info.get("current_bp", info.get("bp", "120/80")),
            hr=info.get("current_hr", info.get("hr", 80)),
            rr=info.get("current_rr", info.get("rr", 16)),
            temp=info.get("current_temp", info.get("temp", 37.0)),
            spo2=info.get("current_spo2", info.get("spo2", 98)),
            physical_exam=info.get("physical_exam", "Not yet examined"),
            labs=info.get("labs", "Pending"),
        )

        if self.specialized_knowledge:
            base_prompt += (
                "\n\n=== YOUR CLINICAL PROTOCOL KNOWLEDGE ===\n"
                "Use this specialized knowledge for accurate clinical observations, "
                "nursing assessments, and protocol-based responses specific to this condition.\n\n"
                f"{self.specialized_knowledge}"
            )

        return base_prompt

    def get_fallback_response(self, message: str, case_context: dict) -> str:
        msg = message.lower()
        vitals = self.case_info

        if self.urgency_level == "critical":
            return (
                f"Doctor! Patient's vitals are concerning — "
                f"HR {vitals['hr']}, SpO2 {vitals['spo2']}%, RR {vitals['rr']}. "
                f"We need to act quickly. What do you want me to start?"
            )

        if any(w in msg for w in ["vitals", "vital signs", "bp", "pulse"]):
            return (
                f"Doctor, latest vitals: BP {vitals['bp']}, HR {vitals['hr']} bpm, "
                f"RR {vitals['rr']}/min, Temp {vitals['temp']}°C, SpO2 {vitals['spo2']}%. "
                f"{'I notice the SpO2 is on the lower side.' if vitals['spo2'] < 95 else 'Vitals are noted.'}"
            )

        if any(w in msg for w in ["oxygen", "o2", "spo2"]):
            return (
                f"SpO2 is currently {vitals['spo2']}%. "
                f"{'Shall I start supplemental O2 via nasal cannula?' if vitals['spo2'] < 94 else 'Saturation is being maintained.'}"
            )

        if any(w in msg for w in ["iv", "line", "access", "cannula"]):
            return "Doctor, shall I get an IV line set up? I have 18G and 20G cannulas ready. Which access do you want?"

        if any(w in msg for w in ["monitor", "ecg", "cardiac"]):
            return "I'll put the patient on continuous cardiac monitoring right away. ECG machine is on its way."

        if any(w in msg for w in ["lab", "blood", "test", "investigation"]):
            return "Doctor, I can send the samples to lab right away. What tests do you want me to order — CBC, RFT, LFT, or anything specific?"

        if self.urgency_level == "urgent":
            return (
                f"Doctor, just to update you — the patient's HR is {vitals['hr']} and SpO2 {vitals['spo2']}%. "
                f"I'd recommend we keep a close watch. Want me to prepare any emergency medications?"
            )

        return "Yes doctor, I'm here. What do you need me to do for the patient?"

    def get_initial_report(self) -> dict:
        """Generate nurse's initial patient handoff report."""
        vitals = self.case_info
        alerts = []

        if vitals["spo2"] < 94:
            alerts.append(f"SpO2 is low at {vitals['spo2']}%")
        if vitals["hr"] > 110:
            alerts.append(f"tachycardic at {vitals['hr']} bpm")
        if vitals["rr"] > 24:
            alerts.append(f"tachypneic with RR {vitals['rr']}")
        if vitals["temp"] > 38.5:
            alerts.append(f"febrile at {vitals['temp']}°C")

        base = (
            f"Doctor, we have a {vitals['age']}-year-old {vitals['gender'].lower()} patient "
            f"presenting with {vitals['chief_complaint'].lower()}. "
            f"Vitals — BP {vitals['bp']}, HR {vitals['hr']}, RR {vitals['rr']}, "
            f"Temp {vitals['temp']}°C, SpO2 {vitals['spo2']}%."
        )

        if alerts:
            base += f" Please note: patient is {', '.join(alerts)}."

        if self.urgency_level in ("urgent", "critical"):
            base += " I'd recommend we prioritize this case."

        return {
            "agent_type": self.agent_type,
            "display_name": self.display_name,
            "content": base,
            "urgency_level": self.urgency_level,
        }
