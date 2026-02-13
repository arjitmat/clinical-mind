"""Patient agent — speaks in Hindi/English mix with realistic distress levels."""

from app.core.agents.base_agent import BaseAgent


PATIENT_SYSTEM_PROMPT = """You are a patient in an Indian hospital. You are being examined by a medical student.

CRITICAL RULES:
1. You speak in Hindi-English mix (Hinglish) naturally — like a real Indian patient would.
   Examples: "Doctor sahab, mujhe bahut zyada dard ho raha hai chest mein", "Haan doctor, breathing mein problem hai"
2. You do NOT know medical terminology. Describe symptoms in simple, lay terms.
3. You have a specific distress level based on your condition severity.
4. You may be anxious, scared, in pain, or confused — act accordingly.
5. You can only share information you would realistically know (symptoms, history, lifestyle).
6. You do NOT know your own diagnosis. You are the patient, not the doctor.
7. If asked about something you don't know (like lab values), say "Yeh toh doctor aapko pata hoga"
8. Keep responses realistic — 1-3 sentences typically, more if telling your history.

PATIENT DETAILS:
- Age: {age}, Gender: {gender}, Location: {location}
- Chief complaint: {chief_complaint}
- Presentation: {presentation}
- History: {history}
- Distress level: {distress_level} (low=calm, moderate=worried, high=distressed/crying, critical=severe pain/panic)

DISTRESS BEHAVIOR:
- low: Calm, answers questions clearly. "Haan doctor, yeh problem 2 hafte se hai."
- moderate: Worried but cooperative. "Doctor, mujhe dar lag raha hai... kuch serious toh nahi?"
- high: In visible distress, may cry or groan. "Aaahhh... bahut dard ho raha hai doctor... please kuch karo!"
- critical: Severe pain/panic, short responses. "Doctor... saans... nahi aa rahi... please..."

Respond ONLY as the patient. Stay in character completely."""


class PatientAgent(BaseAgent):
    """Patient agent that speaks in Hinglish with realistic distress."""

    agent_type = "patient"
    display_name = "Patient"

    def __init__(self):
        super().__init__()
        self.distress_level = "moderate"
        self.patient_info: dict = {}

    def configure(self, case_data: dict):
        """Configure patient with case-specific data."""
        self.patient_info = {
            "age": case_data.get("patient", {}).get("age", 45),
            "gender": case_data.get("patient", {}).get("gender", "Male"),
            "location": case_data.get("patient", {}).get("location", "Delhi"),
            "chief_complaint": case_data.get("chief_complaint", ""),
            "presentation": case_data.get("initial_presentation", ""),
            "history": "",
        }

        # Extract history from stages
        for stage in case_data.get("stages", []):
            if stage.get("stage") == "history":
                self.patient_info["history"] = stage.get("info", "")
                break

        # Set distress based on vital signs and difficulty
        self._set_distress_level(case_data)

    def _set_distress_level(self, case_data: dict):
        """Determine distress level from vitals and difficulty."""
        difficulty = case_data.get("difficulty", "intermediate")
        vitals = case_data.get("vital_signs", {})

        hr = vitals.get("hr", 80)
        spo2 = vitals.get("spo2", 98)
        rr = vitals.get("rr", 16)

        if difficulty == "advanced" or spo2 < 90 or hr > 130 or rr > 30:
            self.distress_level = "critical"
        elif difficulty == "intermediate" or spo2 < 94 or hr > 110 or rr > 24:
            self.distress_level = "high"
        elif hr > 100 or rr > 20:
            self.distress_level = "moderate"
        else:
            self.distress_level = "low"

    def get_system_prompt(self, case_context: dict) -> str:
        info = {**self.patient_info, **case_context}
        info["distress_level"] = self.distress_level
        return PATIENT_SYSTEM_PROMPT.format(
            age=info.get("age", 45),
            gender=info.get("gender", "Male"),
            location=info.get("location", "Delhi"),
            chief_complaint=info.get("chief_complaint", "unknown"),
            presentation=info.get("presentation", ""),
            history=info.get("history", ""),
            distress_level=self.distress_level,
        )

    def get_fallback_response(self, message: str, case_context: dict) -> str:
        msg = message.lower()

        if self.distress_level == "critical":
            if any(w in msg for w in ["pain", "dard", "hurt"]):
                return "Doctor... bahut... zyada dard... please kuch karo... saans nahi aa rahi..."
            return "Doctor... please... jaldi..."

        if self.distress_level == "high":
            if any(w in msg for w in ["how long", "kab se", "when"]):
                return "Doctor sahab, yeh 2-3 din se bahut zyada ho gaya hai... pehle thoda thoda hota tha, ab toh sehen nahi hota!"
            if any(w in msg for w in ["pain", "dard", "hurt"]):
                return "Haan doctor, bahut dard hai... yahan pe... aaahhh... please dawai de do!"
            return "Doctor, mujhe bahut takleef ho rahi hai... kuch serious toh nahi na?"

        if self.distress_level == "moderate":
            if any(w in msg for w in ["history", "pehle", "before", "past"]):
                return "Doctor, pehle aisa kabhi nahi hua tha. Bas 1-2 baar thoda sa hua tha lekin itna nahi tha."
            if any(w in msg for w in ["medicine", "dawai", "medication"]):
                return "Haan doctor, mein BP ki dawai leta hoon... naam yaad nahi aa raha... chhoti wali goli hai."
            if any(w in msg for w in ["family", "gharwale", "parents"]):
                return "Ji doctor, mere father ko bhi sugar tha... aur unko heart ka bhi problem tha."
            return "Ji doctor, bataiye kya karna hai? Mujhe thoda dar lag raha hai."

        # low distress
        if any(w in msg for w in ["how", "kaise"]):
            return "Doctor sahab, yeh problem thode dinon se hai. Pehle chalta tha lekin ab zyada ho gaya."
        if any(w in msg for w in ["smoke", "drink", "sharab", "cigarette"]):
            return "Nahi doctor, mein na pita hoon na cigarette peeta hoon. Bas kabhi kabhi chai peeta hoon."
        return f"Ji doctor, main {self.patient_info.get('chief_complaint', 'problem').lower()} ki wajah se aaya hoon. Aap bataiye kya karna chahiye?"

    def get_initial_greeting(self) -> dict:
        """Generate the patient's initial complaint on arrival."""
        cc = self.patient_info.get("chief_complaint", "problem")
        age = self.patient_info.get("age", 45)
        gender = self.patient_info.get("gender", "Male")
        honorific = "beti" if gender == "Female" and age < 30 else "bhai" if gender == "Male" and age < 40 else "uncle" if gender == "Male" else "aunty"

        greetings = {
            "critical": f"Doctor sahab... please... {cc.lower()}... bahut... zyada hai... saans nahi aa rahi...",
            "high": f"Doctor sahab, namaste... mujhe bahut zyada problem ho rahi hai... {cc.lower()}... please jaldi check karo!",
            "moderate": f"Namaste doctor sahab. Mein aapke paas aaya hoon kyunki mujhe {cc.lower()} ki problem hai. 2-3 din se ho raha hai, ab zyada ho gaya.",
            "low": f"Namaste doctor sahab. Mujhe {cc.lower()} ki thodi si problem hai, isliye aaya hoon. Dekhiye na please.",
        }

        content = greetings.get(self.distress_level, greetings["moderate"])
        return {
            "agent_type": self.agent_type,
            "display_name": self.display_name,
            "content": content,
            "distress_level": self.distress_level,
        }
