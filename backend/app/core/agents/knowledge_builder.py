"""Dynamic knowledge builder — uses RAG + Claude to create role-specific expertise per case.

When a gastritis case arrives:
- Patient agent learns: how gastritis feels to a layperson, realistic symptom descriptions in Hinglish
- Nurse agent learns: nursing protocols for gastritis, what vitals to monitor, when to escalate
- Senior doctor learns: differential diagnosis algorithm, Indian guidelines (API/ICMR), NEET-PG patterns

This is what makes each agent a genuine specialist for the current case, not a generic responder.
"""

import logging
import os
from typing import Optional

import anthropic

from app.core.rag.vector_store import MedicalVectorStore
from app.core.rag.retriever import MedicalRetriever

logger = logging.getLogger(__name__)

# ---- Role-specific synthesis prompts ----

PATIENT_KNOWLEDGE_PROMPT = """You are a medical knowledge synthesizer. Given the clinical reference material below about a specific condition/case, create a PATIENT EXPERIENCE PROFILE that a patient agent can use to realistically roleplay this condition.

{rag_context}

CURRENT CASE:
- Diagnosis: {diagnosis}
- Specialty: {specialty}
- Chief complaint: {chief_complaint}
- Presentation: {presentation}

Synthesize this into a patient experience profile. Write in second person ("you feel...") as instructions for the patient agent:

1. SYMPTOM EXPERIENCE: How does this condition feel to a layperson? Describe the pain, discomfort, sensations in simple Hindi-English terms a real Indian patient would use. Be specific — "chest mein jalan hoti hai khana khane ke baad" not just "chest pain".

2. SYMPTOM TIMELINE: How did symptoms develop? What happened first, what got worse? When did the patient decide to come to the hospital?

3. PERSONAL HISTORY: Realistic lifestyle details for an Indian patient with this condition — diet (spicy food, chai, gutka?), work stress, family history patterns common in India.

4. WHAT PATIENT KNOWS vs DOESN'T: What would this patient realistically know about their condition? What misconceptions might they have? (e.g., "Mujhe laga gas ki problem hai")

5. EMOTIONAL STATE: Based on severity — is the patient scared? In denial? Frustrated because "dawai kha raha hoon par theek nahi ho raha"?

6. RESPONSES TO COMMON QUESTIONS: How would this patient respond to standard history-taking questions (onset, duration, aggravating/relieving factors, associated symptoms)?

Keep it concise but specific to THIS condition. Write in a mix of English and Hindi as the patient would speak."""

NURSE_KNOWLEDGE_PROMPT = """You are a medical knowledge synthesizer. Given the clinical reference material below, create a NURSING PROTOCOL BRIEF that a nurse agent can use to realistically assist in managing this case in an Indian hospital setting.

{rag_context}

CURRENT CASE:
- Diagnosis: {diagnosis}
- Specialty: {specialty}
- Vital signs: BP {bp}, HR {hr}, RR {rr}, Temp {temp}°C, SpO2 {spo2}%
- Chief complaint: {chief_complaint}

Synthesize into a nursing protocol brief:

1. TRIAGE ASSESSMENT: Based on these vitals and presentation, what is the triage category? What are the RED FLAGS the nurse should watch for?

2. MONITORING PRIORITIES: What specific parameters need close monitoring? How often? What changes would indicate deterioration?

3. IMMEDIATE NURSING ACTIONS: What should the nurse prepare/initiate even before the doctor's orders? (IV access, O2, positioning, monitoring)

4. EXPECTED INVESTIGATIONS: What labs/tests will likely be ordered? What samples should be ready? What equipment is needed?

5. MEDICATION AWARENESS: What medications are commonly used for this condition in Indian hospitals? What should the nurse have ready? Any contraindications to watch for?

6. CLINICAL OBSERVATIONS: What specific physical signs should the nurse report to the doctor? What nursing assessment findings are critical?

7. EMERGENCY PREPAREDNESS: If this patient deteriorates, what emergency equipment/medications should be at bedside?

8. INDIAN HOSPITAL CONTEXT: Any specific considerations for Indian government hospital setting — bed availability, referral protocols, commonly available drugs.

Be specific to THIS case. Use proper medical terminology as an experienced Indian ward nurse would."""

SENIOR_KNOWLEDGE_PROMPT = """You are a medical knowledge synthesizer. Given the clinical reference material below, create a TEACHING & DIAGNOSTIC EXPERTISE BRIEF that a senior consultant can use to guide a medical student through this case using the Socratic method.

{rag_context}

CURRENT CASE:
- Diagnosis: {diagnosis}
- Specialty: {specialty}
- Difficulty: {difficulty}
- Chief complaint: {chief_complaint}
- Key differentials: {differentials}
- Learning points: {learning_points}

Synthesize into a teaching expertise brief:

1. DIAGNOSTIC ALGORITHM: Step-by-step clinical reasoning path for this case. What findings point toward the diagnosis? What rules out the key differentials? Include the "golden finding" — the single most specific clue.

2. DIFFERENTIAL DIAGNOSIS MATRIX: For each major differential, list:
   - What findings SUPPORT it
   - What findings ARGUE AGAINST it
   - The ONE investigation that distinguishes it

3. INDIAN EPIDEMIOLOGY: Prevalence and patterns in India. Why is this condition important in Indian context? Risk factors specific to Indian population (diet, lifestyle, genetic).

4. INDIAN GUIDELINES: Relevant ICMR, API (Association of Physicians of India), NHM, or specialty-specific Indian guidelines for management. Standard of care in Indian teaching hospitals.

5. NEET-PG EXAM RELEVANCE: How is this condition typically tested? Common question patterns. High-yield facts that students must know. Classic "one-liner" descriptions used in exams.

6. SOCRATIC TEACHING PLAN:
   - 3 progressive Socratic questions to guide the student (easy → hard)
   - Key hints to give if student is stuck (without revealing diagnosis)
   - How to redirect if student is on wrong track
   - Teaching points to cover AFTER diagnosis is made

7. PATHOPHYSIOLOGY DEPTH: The mechanism of disease that explains ALL the clinical findings. How to connect symptoms → signs → investigation findings through pathophysiology.

8. MANAGEMENT OVERVIEW: First-line treatment, Indian-context alternatives, monitoring plan, disposition.

Be comprehensive but focused on THIS specific case. Reference Indian medical education context throughout."""


class DynamicKnowledgeBuilder:
    """Builds role-specific medical expertise dynamically using RAG + Claude synthesis.

    For each case, queries the medical corpus for relevant knowledge, then uses
    Claude Opus to synthesize it into specialized "skills" for each agent role.
    """

    def __init__(self):
        self.vector_store = MedicalVectorStore()
        self.retriever = MedicalRetriever(self.vector_store)

        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client: Optional[anthropic.Anthropic] = None
        if self.api_key and self.api_key != "sk-ant-your-key-here":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"KnowledgeBuilder Claude init failed: {e}")

        # Cache synthesized knowledge: {(case_id, role): knowledge_str}
        self._cache: dict[tuple[str, str], str] = {}

    def build_knowledge(self, case_data: dict, role: str) -> str:
        """Build role-specific knowledge for a case.

        Args:
            case_data: The full case dict (with id, diagnosis, specialty, etc.)
            role: One of 'patient', 'nurse', 'senior_doctor'

        Returns:
            Synthesized knowledge string to inject into the agent's system prompt.
        """
        case_id = case_data.get("id", "unknown")
        cache_key = (case_id, role)

        # Return cached if available
        if cache_key in self._cache:
            logger.info(f"Knowledge cache hit: {role} for case {case_id}")
            return self._cache[cache_key]

        # Step 1: Gather RAG context
        rag_context = self._gather_rag_context(case_data, role)

        # Step 2: Synthesize with Claude
        knowledge = self._synthesize_knowledge(case_data, role, rag_context)

        # Step 3: Cache and return
        if knowledge:
            self._cache[cache_key] = knowledge
            logger.info(f"Built {role} knowledge for case {case_id} ({len(knowledge)} chars)")

        return knowledge or ""

    def _gather_rag_context(self, case_data: dict, role: str) -> str:
        """Query RAG for role-appropriate medical knowledge."""
        specialty = case_data.get("specialty", "")
        diagnosis = case_data.get("diagnosis", "")
        chief_complaint = case_data.get("chief_complaint", "")

        context_parts = []

        if role == "patient":
            # Get presentation-focused chunks — how conditions present clinically
            query = f"Patient presenting with {chief_complaint}. Symptoms, history, clinical presentation for {diagnosis}"
            results = self.vector_store.query(
                query_text=query,
                specialty=specialty,
                n_results=5,
                chunk_type="presentation",
            )
            if results:
                context_parts.append("=== SIMILAR PATIENT PRESENTATIONS ===")
                for r in results:
                    context_parts.append(r["content"])
                    context_parts.append("")

            # Also get full narratives for richer context
            full_results = self.vector_store.query(
                query_text=f"Clinical case {specialty} {diagnosis}",
                specialty=specialty,
                n_results=3,
                chunk_type="full_narrative",
            )
            if full_results:
                context_parts.append("=== REFERENCE CASES ===")
                for r in full_results:
                    context_parts.append(r["content"])
                    context_parts.append("")

        elif role == "nurse":
            # Get full clinical cases for nursing protocol context
            query = f"Clinical management of {diagnosis}. Vital signs, monitoring, nursing assessment, emergency protocols for {chief_complaint}"
            results = self.vector_store.query(
                query_text=query,
                specialty=specialty,
                n_results=5,
                chunk_type="full_narrative",
            )
            if results:
                context_parts.append("=== CLINICAL REFERENCE FOR NURSING PROTOCOLS ===")
                for r in results:
                    context_parts.append(r["content"])
                    context_parts.append("")

            # Get learning material for clinical knowledge
            learning_results = self.vector_store.query(
                query_text=f"Diagnosis and management: {diagnosis}",
                specialty=specialty,
                n_results=3,
                chunk_type="learning",
            )
            if learning_results:
                context_parts.append("=== DIAGNOSTIC & LEARNING MATERIAL ===")
                for r in learning_results:
                    context_parts.append(r["content"])
                    context_parts.append("")

        elif role == "senior_doctor":
            # Get everything — full cases, learning, presentations
            for chunk_type, label, n in [
                ("full_narrative", "COMPLETE CASE REFERENCES", 5),
                ("learning", "DIAGNOSTIC & TEACHING MATERIAL", 5),
                ("presentation", "CLINICAL PRESENTATIONS", 3),
            ]:
                query = f"{diagnosis} differential diagnosis pathophysiology management {specialty}"
                results = self.vector_store.query(
                    query_text=query,
                    specialty=specialty,
                    n_results=n,
                    chunk_type=chunk_type,
                )
                if results:
                    context_parts.append(f"=== {label} ===")
                    for r in results:
                        context_parts.append(r["content"])
                        context_parts.append("")

        return "\n".join(context_parts) if context_parts else ""

    def _synthesize_knowledge(
        self, case_data: dict, role: str, rag_context: str
    ) -> Optional[str]:
        """Use Claude Opus with extended thinking to synthesize role-specific expertise."""
        if not self.client:
            logger.warning("No Claude client — returning RAG context as-is for knowledge")
            return self._fallback_knowledge(case_data, role, rag_context)

        # Select the role-specific synthesis prompt
        prompts = {
            "patient": PATIENT_KNOWLEDGE_PROMPT,
            "nurse": NURSE_KNOWLEDGE_PROMPT,
            "senior_doctor": SENIOR_KNOWLEDGE_PROMPT,
        }
        prompt_template = prompts.get(role)
        if not prompt_template:
            return None

        # Build the synthesis prompt
        vitals = case_data.get("vital_signs", {})
        prompt = prompt_template.format(
            rag_context=rag_context or "No RAG context available — use your medical knowledge.",
            diagnosis=case_data.get("diagnosis", "unknown"),
            specialty=case_data.get("specialty", "general"),
            difficulty=case_data.get("difficulty", "intermediate"),
            chief_complaint=case_data.get("chief_complaint", ""),
            presentation=case_data.get("initial_presentation", ""),
            differentials=", ".join(case_data.get("differentials", [])),
            learning_points="; ".join(case_data.get("learning_points", [])),
            bp=vitals.get("bp", "120/80"),
            hr=vitals.get("hr", 80),
            rr=vitals.get("rr", 16),
            temp=vitals.get("temp", 37.0),
            spo2=vitals.get("spo2", 98),
        )

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=8000,
                temperature=1,  # required for extended thinking
                thinking={
                    "type": "enabled",
                    "budget_tokens": 8000,
                },
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract the text content (skip thinking blocks)
            content = ""
            for block in response.content:
                if block.type == "text":
                    content = block.text.strip()

            if content:
                logger.info(f"Synthesized {role} knowledge: {len(content)} chars")
                return content

        except Exception as e:
            logger.error(f"Knowledge synthesis error for {role}: {e}")

        return self._fallback_knowledge(case_data, role, rag_context)

    def _fallback_knowledge(
        self, case_data: dict, role: str, rag_context: str
    ) -> str:
        """Fallback when Claude is unavailable — return structured RAG context."""
        diagnosis = case_data.get("diagnosis", "")
        specialty = case_data.get("specialty", "")
        chief_complaint = case_data.get("chief_complaint", "")

        if role == "patient":
            return (
                f"CONDITION KNOWLEDGE:\n"
                f"You are presenting with {chief_complaint}.\n"
                f"The underlying condition is related to {specialty}.\n"
                f"Describe your symptoms in simple Hinglish terms.\n"
                f"You have been experiencing these symptoms and they brought you to the hospital.\n\n"
                f"REFERENCE MATERIAL:\n{rag_context[:2000]}"
            )

        if role == "nurse":
            vitals = case_data.get("vital_signs", {})
            return (
                f"CLINICAL PROTOCOL KNOWLEDGE:\n"
                f"Patient presenting with {chief_complaint} ({specialty}).\n"
                f"Vitals: BP {vitals.get('bp')}, HR {vitals.get('hr')}, "
                f"RR {vitals.get('rr')}, SpO2 {vitals.get('spo2')}%.\n"
                f"Monitor vitals closely. Prepare for standard investigations.\n"
                f"Have emergency cart ready if vitals deteriorate.\n\n"
                f"REFERENCE MATERIAL:\n{rag_context[:2000]}"
            )

        if role == "senior_doctor":
            return (
                f"TEACHING KNOWLEDGE:\n"
                f"Case: {chief_complaint} ({specialty})\n"
                f"Diagnosis: {diagnosis}\n"
                f"Differentials: {', '.join(case_data.get('differentials', []))}\n"
                f"Learning points: {'; '.join(case_data.get('learning_points', []))}\n"
                f"Guide the student using Socratic method.\n\n"
                f"REFERENCE MATERIAL:\n{rag_context[:3000]}"
            )

        return rag_context[:2000] if rag_context else ""


# Singleton instance
knowledge_builder = DynamicKnowledgeBuilder()
