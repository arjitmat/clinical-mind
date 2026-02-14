"""Family member agent — brings cultural context, emotional pressure, and additional history in Hinglish."""

from app.core.agents.base_agent import BaseAgent


FAMILY_SYSTEM_PROMPT = """You are a family member of a patient in an Indian government hospital. A medical student (junior doctor) is examining your relative.

CRITICAL RULES:
1. You speak in Hindi-English mix (Hinglish) naturally — like a real Indian family member would.
   Examples: "Doctor sahab, please inka kuch karo!", "Hum bahut pareshan hain doctor", "Private mein bahut kharcha ho gaya"
2. You do NOT know medical terminology. You describe things in lay terms.
3. You are emotionally invested — worried, anxious, sometimes pushy or tearful.
4. You may speak FOR the patient, interrupt, or add details the patient forgot.
5. You may withhold embarrassing information initially (alcoholism, mental health, family disputes).
6. You provide cultural context: dietary habits, home remedies tried, religious beliefs.
7. Keep responses realistic — 2-4 sentences typically, more when telling the backstory.
8. NEVER reveal information beyond the case data. If asked something not in the history, say "Humein nahi pata doctor" or "Yeh toh inhone kabhi bataya nahi."
9. You may contradict the patient's story slightly — this is realistic family dynamics.

YOUR RELATIONSHIP: {relationship} of the patient

REALISTIC INDIAN FAMILY BEHAVIORS:
- You tried home remedies first: haldi doodh, kadha, Vicks ki malish, desi ghee, neem ka paani
- You took the patient to a local RMP / jhola-chhaap doctor who gave injections and "drip" but nothing worked
- You may bring outside opinions: "Padosi ne kaha ki yeh typhoid hai", "WhatsApp pe padha ki yeh cancer ho sakta hai"
- You came to govt hospital because private was too expensive: "Private mein 50,000 laga diye, kuch nahi hua"
- You are overprotective: may answer questions directed at the patient, hover, get emotional
- Cost concerns are always present: "Doctor, kitna kharcha hoga?", "Hum garib log hain", "Insurance nahi hai"
- Work/livelihood concerns: "Yeh akele kamane wale hain", "Dukaan band hai 5 din se"
- Religious/cultural: "Mandir mein mannat maangi hai", "Maulvi sahab ne dum karwaya tha", "Gurudwara se langar leke aaye hain"
- Family medical history shared (sometimes reluctantly): "Inka papa ko bhi sugar thi", "Ghar mein sabko BP hai"
- May pressure the doctor: "Doctor kuch karo na please!", "Itna time kyun lag raha hai?"
- May bring food against medical advice: "Thoda doodh pilane mein kya hai doctor?"
- May question everything: "Yeh kitni dawaiyan de rahe ho?", "Injection zaruri hai kya?"
- May get emotional: "Agar inko kuch ho gaya toh...", crying, pleading
- May blame the patient: "Maine kaha tha sharab mat piyo!", "Khana time pe nahi khate"
- May share TMI: "Doctor, inki shaadi mein bhi problem hai", oversharing personal details
- May ask about diet repeatedly: "Kya khila sakte hain?", "Chai de sakte hain kya?"

PATIENT DETAILS:
- Patient age: {patient_age}, Gender: {patient_gender}, Location: {location}
- Chief complaint: {chief_complaint}
- Presentation: {presentation}
- History: {history}
- Family history: {family_history}

EMOTIONAL STATE:
- {emotional_state}

CULTURAL CONTEXT:
- Location-based: {location} — adjust dialect and cultural references accordingly
- Socioeconomic: Government hospital implies middle/lower-middle class
- You may reference local beliefs and practices specific to the region

Respond ONLY as the family member. Stay in character completely. Be emotionally authentic."""


class FamilyAgent(BaseAgent):
    """Family member agent that provides cultural context and emotional pressure in Hinglish."""

    agent_type = "family"
    display_name = "Family Member"

    def __init__(self):
        super().__init__()
        self.emotional_state = "worried"
        self.relationship = "Mother"
        self.family_info: dict = {}

    def configure(self, case_data: dict):
        """Configure family member with case-specific data."""
        patient = case_data.get("patient", {})
        age = patient.get("age", 45)
        gender = patient.get("gender", "Male")
        location = patient.get("location", "Delhi")

        # Choose appropriate family relationship based on patient demographics
        self.relationship = self._choose_relationship(age, gender)
        self.display_name = f"Patient's {self.relationship}"

        self.family_info = {
            "patient_age": age,
            "patient_gender": gender,
            "location": location,
            "chief_complaint": case_data.get("chief_complaint", ""),
            "presentation": case_data.get("initial_presentation", ""),
            "history": "",
            "family_history": "",
            "relationship": self.relationship,
        }

        # Extract history and family history from stages
        for stage in case_data.get("stages", []):
            if stage.get("stage") == "history":
                self.family_info["history"] = stage.get("info", "")
            elif stage.get("stage") == "family_history":
                self.family_info["family_history"] = stage.get("info", "")

        # If no dedicated family_history stage, try to extract from general history
        if not self.family_info["family_history"]:
            history_text = self.family_info.get("history", "")
            if "family" in history_text.lower():
                self.family_info["family_history"] = history_text

        # Set emotional state based on case severity
        self._set_emotional_state(case_data)

    def _choose_relationship(self, age: int, gender: str) -> str:
        """Choose realistic family relationship based on patient demographics."""
        if age < 12:
            return "Mother"
        elif age < 18:
            return "Father" if gender == "Male" else "Mother"
        elif age < 30:
            if gender == "Male":
                return "Mother"
            else:
                return "Husband"
        elif age < 50:
            if gender == "Male":
                return "Wife"
            else:
                return "Husband"
        elif age < 65:
            return "Son" if gender == "Male" else "Daughter"
        else:
            return "Son"

    def _set_emotional_state(self, case_data: dict):
        """Determine emotional state from case severity."""
        difficulty = case_data.get("difficulty", "intermediate")
        vitals = case_data.get("vital_signs", {})

        hr = vitals.get("hr", 80)
        spo2 = vitals.get("spo2", 98)

        if difficulty == "advanced" or spo2 < 90 or hr > 130:
            self.emotional_state = (
                "Extremely distressed — crying, pleading with the doctor, "
                "may become irrational or aggressive out of fear. "
                "\"Doctor please inko bacha lo! Kuch bhi karo!\""
            )
        elif difficulty == "intermediate" or spo2 < 94 or hr > 110:
            self.emotional_state = (
                "Very worried — pacing, asking repeated questions, "
                "may pressure the doctor for quick answers. "
                "\"Doctor, kya hua hai inko? Serious toh nahi hai na?\""
            )
        elif hr > 100:
            self.emotional_state = (
                "Worried but cooperative — concerned, hovering near the patient, "
                "providing information when asked. "
                "\"Doctor sahab, hum bahut pareshan hain, batao kya karna hai.\""
            )
        else:
            self.emotional_state = (
                "Concerned but calm — cooperative, answers questions, "
                "provides background information. "
                "\"Ji doctor, aap poochiye, hum sab batayenge.\""
            )

    def get_system_prompt(self, case_context: dict) -> str:
        info = {**self.family_info, **case_context}
        info["emotional_state"] = self.emotional_state
        base_prompt = FAMILY_SYSTEM_PROMPT.format(
            relationship=info.get("relationship", "Mother"),
            patient_age=info.get("patient_age", 45),
            patient_gender=info.get("patient_gender", "Male"),
            location=info.get("location", "Delhi"),
            chief_complaint=info.get("chief_complaint", "unknown"),
            presentation=info.get("presentation", ""),
            history=info.get("history", ""),
            family_history=info.get("family_history", "Not known"),
            emotional_state=self.emotional_state,
        )

        if self.specialized_knowledge:
            base_prompt += (
                "\n\n=== YOUR FAMILY & CULTURAL KNOWLEDGE ===\n"
                "Use this knowledge to realistically portray the family member's perspective. "
                "Express medical concepts as a layperson would understand them — through worry, "
                "cultural beliefs, and family experience, NOT medical terms.\n\n"
                f"{self.specialized_knowledge}"
            )

        return base_prompt

    def get_fallback_response(self, message: str, case_context: dict) -> str:
        msg = message.lower()
        cc = self.family_info.get("chief_complaint", "problem").lower()
        rel = self.relationship.lower()

        # Emotional pressure / urgency
        if any(w in msg for w in ["wait", "time", "kitna", "report", "result"]):
            return (
                "Doctor sahab, kitna aur wait karna padega? Hum subah se yahan baithe hain. "
                "Inki haalat dekho na, bahut takleef mein hain. Please jaldi kuch karo!"
            )

        # History / background questions
        if any(w in msg for w in ["history", "pehle", "before", "past", "earlier"]):
            return (
                f"Doctor, yeh {cc} pehle kabhi nahi hua tha itna. Thoda bahut hota tha, "
                "hum sochte the apne aap theek ho jayega. Local doctor ke paas gaye the, "
                "unhone injection diya aur goli di, 2-3 din theek raha phir wapas ho gaya."
            )

        # Family medical history
        if any(w in msg for w in ["family", "gharwale", "parents", "mother", "father", "hereditary"]):
            family_hist = self.family_info.get("family_history", "")
            if family_hist and family_hist != "Not known":
                return (
                    f"Haan doctor, ghar mein toh hai yeh sab. {family_hist}. "
                    "Humne socha nahi tha ki inko bhi ho jayega."
                )
            return (
                "Doctor, ghar mein toh kisi ko kuch khaas nahi tha... "
                "Inka papa ko thoda BP tha shayad, par woh bhi dawai lete the. "
                "Aur kuch yaad nahi aa raha."
            )

        # Home remedies / what was tried
        if any(w in msg for w in ["remedy", "treatment", "dawai", "medicine", "tried", "kya kiya"]):
            return (
                "Doctor, pehle humne haldi wala doodh diya, phir padosi ne bola ki Hajmola khilao. "
                "Phir chemist se Crocin li, usse thoda aram mila par raat ko phir bura ho gaya. "
                "Tab humne bade hospital aane ka socha."
            )

        # Cost concerns
        if any(w in msg for w in ["cost", "kharcha", "paisa", "money", "expensive", "pay"]):
            return (
                "Doctor sahab, hum already private mein bahut kharcha kar chuke hain. "
                "Isliye yahan aaye hain. Zyada mehnga test mat karwao please, "
                "hum garib log hain... bas inko theek kar do."
            )

        # Diet / food questions
        if any(w in msg for w in ["diet", "food", "khana", "kya khilaye", "eat"]):
            return (
                "Doctor, inko kya khila sakte hain? Doodh de sakte hain? "
                "Chai toh peete hain roz, woh band karna padega kya? "
                "Ghar ka khana laaye hain, thoda dal-chawal hai."
            )

        # Alcohol / smoking / sensitive topics
        if any(w in msg for w in ["smoke", "drink", "sharab", "alcohol", "cigarette", "tobacco", "gutka"]):
            return (
                "Nahi nahi doctor, yeh sab kuch nahi karte... "
                "matlab... kabhi kabhi friends ke saath thodi beer pi lete hain, "
                "par woh toh sab peete hain na. Zyada nahi peete yeh."
            )

        # Work / livelihood concerns
        if any(w in msg for w in ["work", "kaam", "job", "naukri", "chutti"]):
            return (
                "Doctor, yeh akele kamane wale hain ghar mein. "
                "5 din se kaam pe nahi gaye, boss bol raha hai ki chutti nahi milegi aur. "
                "Jaldi theek karo please, nahi toh naukri chali jayegi."
            )

        # Questioning treatment / investigations
        if any(w in msg for w in ["injection", "test", "investigation", "blood", "scan"]):
            return (
                "Doctor, itne sare test zaruri hain kya? Injection lagaoge? "
                "Yeh darte hain injection se. Private wale doctor ne bhi 5-6 test karwaye the, "
                "kuch nahi nikla. Please batao kya zaruri hai."
            )

        # Blaming the patient
        if any(w in msg for w in ["why", "kyun", "reason", "cause", "wajah"]):
            return (
                f"Doctor, maine bahut baar bola tha ki apna khayal rakho. "
                "Khana time pe nahi khate, raat ko der tak jagte hain, "
                "stress lete hain. Par sunte hi nahi hain humari!"
            )

        # Default — general worried family response
        return (
            f"Doctor sahab, please batao inko kya hua hai? "
            f"Yeh {cc} bahut badh gaya hai. Padosi ne bola ki bade hospital chalo, "
            "isliye aaye hain. Aap kuch karo na please, hum bahut pareshan hain!"
        )

    def get_initial_context(self) -> dict:
        """Generate the family member's first statement when they arrive."""
        cc = self.family_info.get("chief_complaint", "problem").lower()
        age = self.family_info.get("patient_age", 45)
        gender = self.family_info.get("patient_gender", "Male")
        location = self.family_info.get("location", "Delhi")
        patient_ref = "yeh" if self.relationship in ("Mother", "Father", "Wife", "Husband") else "mere papa" if self.relationship == "Son" else "meri mummy" if self.relationship == "Daughter" else "yeh"

        greetings = {
            "Mother": (
                f"Doctor sahab, namaste! Mera bachcha bahut bimar hai, {cc} ho raha hai. "
                f"2-3 din se dekh rahe hain, local doctor ke paas bhi gaye the par kuch nahi hua. "
                f"Please doctor, inka kuch karo! Hum bahut pareshan hain."
            ),
            "Father": (
                f"Namaste doctor sahab. Yeh mera {('beta' if gender == 'Male' else 'beti')} hai, "
                f"{age} saal ka hai. {cc.capitalize()} ki problem hai. "
                f"Pehle private mein dikhaya, bahut kharcha hua, ab yahan laaye hain. Dekhiye please."
            ),
            "Wife": (
                f"Doctor sahab, namaste. Yeh mere husband hain, inko {cc} ho raha hai. "
                f"3-4 din se kaam pe bhi nahi ja pa rahe. Maine bola doctor ke paas chalo, "
                f"par sunte nahi. Aaj bahut zyada ho gaya toh laaye hain. Please dekh lo."
            ),
            "Husband": (
                f"Doctor sahab, meri wife ko {cc} ki problem hai. Kaafi dino se hai, "
                f"ghar pe kadha pila rahe the, thoda aram tha par ab bahut badh gaya hai. "
                f"Please jaldi check karo, bacche ghar pe akele hain."
            ),
            "Son": (
                f"Namaste doctor. Yeh mere {('papa' if gender == 'Male' else 'mummy')} hain, "
                f"age {age} hai. {cc.capitalize()} ki problem hai kaafi dino se. "
                f"Pehle batate nahi the, aaj achanak tabiyat bigad gayi toh le aaye. "
                f"Please achhe se check kar lo."
            ),
            "Daughter": (
                f"Doctor sahab, yeh meri {('mummy' if gender == 'Female' else 'papa')} hain. "
                f"Inko {cc} ho raha hai, bohot dino se. Dawai lene mein aanakaani karte hain, "
                f"humne zabardasti hospital laaya hai. Please inka dhyan se treatment karo."
            ),
        }

        content = greetings.get(
            self.relationship,
            (
                f"Doctor sahab, namaste. {patient_ref} ko {cc} hai. "
                f"Bahut pareshan hain hum, please jaldi dekh lo."
            ),
        )

        return {
            "agent_type": self.agent_type,
            "display_name": self.display_name,
            "content": content,
            "relationship": self.relationship,
            "emotional_state": self.emotional_state,
        }
