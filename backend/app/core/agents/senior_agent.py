"""Senior doctor agent — Socratic teaching mentor who guides without giving answers."""

from app.core.agents.base_agent import BaseAgent


SENIOR_SYSTEM_PROMPT = """You are a senior consultant doctor (professor) in an Indian teaching hospital. You are supervising a final-year MBBS student who is handling a case.

CRITICAL RULES:
1. Use the SOCRATIC METHOD — ask probing questions, never give the answer directly.
2. Guide the student's clinical reasoning through structured questioning.
3. You are supportive but academically rigorous.
4. You reference Indian clinical guidelines (ICMR, API, NHM) when relevant.
5. You know the correct diagnosis but must NOT reveal it unless the student has already diagnosed correctly.
6. If the student is on the wrong track, gently redirect with questions.
7. If the student is stuck, provide progressive hints (never the answer).
8. Occasionally reference exam relevance: "This is a common NEET-PG question pattern."
9. Keep responses concise — 2-4 sentences with 1-2 Socratic questions.
10. You speak in professional English with occasional Hindi phrases natural in Indian hospitals.

CASE DETAILS:
- Patient: {age}y {gender}, {chief_complaint}
- Specialty: {specialty}
- Difficulty: {difficulty}
- Correct diagnosis: {diagnosis}
- Key differentials: {differentials}
- Critical learning points: {learning_points}

TEACHING APPROACH:
1. If student hasn't started: "Let's approach this systematically. What are your initial impressions?"
2. If student has a hypothesis: Challenge it. "Good thinking, but what else could present similarly?"
3. If student is stuck: Hint progressively. "Think about the vital signs... what pattern do you see?"
4. If student is close: Encourage. "You're on the right track. Now, what investigation would confirm?"
5. If student is wrong: Redirect gently. "That's a reasonable thought, but consider — would that explain ALL the findings?"
6. After diagnosis: Teach the deeper lesson. "Excellent. Now for the exam — what's the pathophysiology here?"

Respond ONLY as the senior doctor. Be a great teacher."""


class SeniorDoctorAgent(BaseAgent):
    """Senior doctor agent that teaches using Socratic method."""

    agent_type = "senior_doctor"
    display_name = "Dr. Sharma"

    def __init__(self):
        super().__init__()
        self.case_info: dict = {}
        self.hints_given = 0
        self.student_on_track = False

    def configure(self, case_data: dict):
        """Configure senior doctor with full case knowledge."""
        self.case_info = {
            "age": case_data.get("patient", {}).get("age", 45),
            "gender": case_data.get("patient", {}).get("gender", "Male"),
            "chief_complaint": case_data.get("chief_complaint", ""),
            "specialty": case_data.get("specialty", ""),
            "difficulty": case_data.get("difficulty", "intermediate"),
            "diagnosis": case_data.get("diagnosis", ""),
            "differentials": ", ".join(case_data.get("differentials", [])[:5]),
            "learning_points": "; ".join(case_data.get("learning_points", [])[:3]),
        }
        self.hints_given = 0
        self.student_on_track = False

    def get_system_prompt(self, case_context: dict) -> str:
        info = {**self.case_info, **case_context}
        return SENIOR_SYSTEM_PROMPT.format(
            age=info.get("age", 45),
            gender=info.get("gender", "Male"),
            chief_complaint=info.get("chief_complaint", "unknown"),
            specialty=info.get("specialty", "general"),
            difficulty=info.get("difficulty", "intermediate"),
            diagnosis=info.get("diagnosis", "unknown"),
            differentials=info.get("differentials", ""),
            learning_points=info.get("learning_points", ""),
        )

    def get_fallback_response(self, message: str, case_context: dict) -> str:
        msg = message.lower()
        self.hints_given += 1

        # Check if student mentions the correct diagnosis
        diagnosis = self.case_info.get("diagnosis", "").lower()
        if diagnosis and any(
            word in msg for word in diagnosis.split() if len(word) > 3
        ):
            self.student_on_track = True
            return (
                "Excellent clinical reasoning! You've identified the key diagnosis. "
                "Now tell me — what is the pathophysiological mechanism here? "
                "And what would be your first-line management according to current guidelines?"
            )

        if self.hints_given <= 1:
            return (
                "Let's think about this systematically. "
                f"You have a {self.case_info.get('age', 45)}-year-old presenting with "
                f"{self.case_info.get('chief_complaint', 'these symptoms')}. "
                "What are the most dangerous diagnoses you need to rule out first? "
                "Start with your differential — what's at the top of your list?"
            )

        if self.hints_given == 2:
            return (
                "Good effort. Now look at the vital signs carefully — do you see a pattern? "
                f"This is a {self.case_info.get('specialty', 'clinical')} case. "
                "What investigation would help you narrow down your differential? "
                "Remember — systematic approach is key for NEET-PG as well."
            )

        if self.hints_given == 3:
            specialty = self.case_info.get("specialty", "")
            return (
                f"Let me give you a hint — think about the classic {specialty} presentations. "
                f"The key differentials here would include: {self.case_info.get('differentials', 'several possibilities')}. "
                "Which of these fits best with ALL the findings — history, examination, and investigations?"
            )

        # Progressive hints after 3
        return (
            "You're working hard on this, which is good. Let me narrow it down — "
            "focus on the ONE finding that is most specific. "
            "What single investigation or sign points you toward the diagnosis? "
            "Think about what makes this case different from the usual presentation."
        )

    def get_initial_guidance(self) -> dict:
        """Generate senior doctor's initial teaching prompt."""
        difficulty = self.case_info.get("difficulty", "intermediate")
        specialty = self.case_info.get("specialty", "clinical")

        if difficulty == "advanced":
            content = (
                f"Interesting {specialty} case we have here. "
                "This one will test your clinical reasoning — the presentation may not be straightforward. "
                "Start by taking a thorough history from the patient. What would you ask first, and why?"
            )
        elif difficulty == "beginner":
            content = (
                f"Good, let's work through this {specialty} case together. "
                "Start from the basics — look at the patient's presentation and vital signs. "
                "What's your initial assessment? Don't worry about getting it perfect, just think aloud."
            )
        else:
            content = (
                f"Alright, we have a {specialty} case. "
                "I want you to approach this like you would in your exam — systematically. "
                "Start with the patient's presenting complaint and vitals. What catches your attention?"
            )

        return {
            "agent_type": self.agent_type,
            "display_name": self.display_name,
            "content": content,
        }
