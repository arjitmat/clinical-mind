"""Dynamic knowledge builder — uses RAG + Claude to create role-specific expertise per case.

ACCURACY PRINCIPLES:
1. ONLY state facts that are grounded in the RAG corpus or well-established medical knowledge
2. Every clinical claim must be traceable to a source (corpus case, named guideline, or textbook)
3. When uncertain, explicitly say so — "This needs verification" is better than a confident wrong answer
4. Indian hospital context must reflect REAL govt hospital workflows, not idealized textbook scenarios
5. Agents must never invent guidelines, statistics, or protocols

Source hierarchy (most to least trusted):
- Named Indian guidelines: ICMR, API, CSI, INASL, ISCCM, NVBDCP/NCVBDC, NACO, IAP, FOGSI
- Indian medical journals: JAPI, IJMR, Indian Heart Journal, Indian J Gastroenterology
- RAG corpus cases (with source attribution)
- Standard medical textbooks: Harrison's, Robbins, Bailey & Love, OP Ghai, DC Dutta
- Well-established clinical consensus (must be labelled as such)
"""

import logging
import os
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

import anthropic

from app.core.rag.vector_store import MedicalVectorStore
from app.core.rag.retriever import MedicalRetriever

logger = logging.getLogger(__name__)

# ---- Grounding rules injected into every synthesis prompt ----

SOURCE_GROUNDING_RULES = """
STRICT ACCURACY RULES — VIOLATIONS ARE UNACCEPTABLE:

1. ONLY USE INFORMATION FROM:
   a) The reference material provided below (RAG corpus)
   b) Well-established medical facts from standard Indian textbooks (Harrison's, Robbins, Park's PSM, OP Ghai)
   c) Named Indian guidelines you are CERTAIN exist: ICMR, API, CSI, INASL, ISCCM, NVBDCP, NACO, IAP, FOGSI, NHM
   d) Named Indian journals: JAPI, IJMR, Indian Heart Journal

2. NEVER:
   - Invent a guideline or protocol that doesn't exist
   - Cite a specific statistic unless it's in the reference material or you are >95% confident
   - State "ICMR recommends X" unless you are certain ICMR actually recommends X
   - Fabricate drug dosages — if unsure, say "dose per institutional protocol"
   - Assume resource availability — Indian govt hospitals often lack CT, MRI, certain drugs

3. WHEN UNCERTAIN, SAY SO:
   - "Per standard teaching hospital protocol..." (when exact guideline unclear)
   - "Commonly practiced in Indian hospitals..." (when no specific guideline)
   - "Verify current dosing with hospital formulary" (when dose uncertain)
   - "Exact prevalence data varies by region" (when stats uncertain)

4. SOURCE ATTRIBUTION:
   - Tag each clinical fact with its source: [Corpus], [Harrison's], [API Guidelines], [Clinical consensus]
   - If a fact comes from the reference material below, tag it [Corpus: CASE-ID] where possible
   - If it's standard textbook knowledge, tag it [Textbook]
   - If it's from a named guideline, tag it [Guideline: NAME]

5. INDIAN HOSPITAL REALITY (not textbook fantasy):
   - Govt hospital: 1 doctor per 50+ patients, overworked nurses, limited beds
   - Often no CT/MRI — rely on clinical skills + basic labs + X-ray + ultrasound
   - Drug availability: generic drugs, NLEM (National List of Essential Medicines)
   - Referral system: PHC → CHC → District Hospital → Medical College Hospital
   - Common constraints: power cuts, blood bank shortages, delayed lab reports
   - Patient reality: delayed presentation (came after trying home remedies/local doctor/ayurvedic)
"""

# ---- Role-specific synthesis prompts ----

PATIENT_KNOWLEDGE_PROMPT = """You are building a PATIENT EXPERIENCE PROFILE for a clinical simulation agent.

{grounding_rules}

REFERENCE MATERIAL FROM MEDICAL CORPUS:
{rag_context}

CURRENT CASE:
- Diagnosis: {diagnosis}
- Specialty: {specialty}
- Chief complaint: {chief_complaint}
- Presentation: {presentation}

Create a patient experience profile grounded ONLY in the reference material and established clinical knowledge.
Write in second person ("you feel...") as instructions for the patient agent:

1. SYMPTOM EXPERIENCE [Source-tagged]:
   How this condition actually feels. Use Hinglish — "pet mein jalan", "saans phoolna", "haath pair sunn hona".
   Be specific to THIS diagnosis from the reference material. Tag sources.

2. SYMPTOM TIMELINE [Source-tagged]:
   Realistic timeline based on the case presentation. Indian patients typically delay — "pehle socha gas hai",
   "local doctor ne antacid di par kaam nahi kiya", "2-3 din wait kiya phir aaya".

3. PATIENT BACKGROUND [Based on Indian demographics]:
   Realistic for the patient's age/gender/location from the case data.
   - Diet: based on region (North Indian = roti/ghee/chai, South = rice/sambar, etc.)
   - Habits: common risk factors for this condition in Indian population
   - Home remedies tried: "haldi wala doodh piya", "Hajmola khaya", "jhadu-phoonk karwaya"
   Only include what's relevant to THIS condition.

4. WHAT PATIENT KNOWS vs DOESN'T:
   - Knows: symptoms they feel, what local doctor said, what family members suggested
   - Doesn't know: medical terms, lab values, their actual diagnosis
   - Misconceptions: common ones for this condition in India (e.g., "heart attack = gas")

5. EMOTIONAL STATE:
   Based on case severity and Indian cultural context.
   - Male patients may minimize symptoms ("kuch nahi hoga")
   - Female patients may worry about family impact ("bacche kaun dekhega")
   - Elderly may be fatalistic ("upar wale ki marzi")

6. RESPONSES TO HISTORY QUESTIONS [Source-tagged]:
   Grounded in the case presentation data. Only answer what this patient would realistically know.
   If the student asks about something not in the case data, the patient should say "pata nahi doctor"."""

NURSE_KNOWLEDGE_PROMPT = """You are building a NURSING PROTOCOL BRIEF for a clinical simulation agent in an Indian government hospital.

{grounding_rules}

REFERENCE MATERIAL FROM MEDICAL CORPUS:
{rag_context}

CURRENT CASE:
- Diagnosis: {diagnosis}
- Specialty: {specialty}
- Vital signs: BP {bp}, HR {hr}, RR {rr}, Temp {temp}°C, SpO2 {spo2}%
- Chief complaint: {chief_complaint}

Create a nursing protocol brief. EVERY clinical action must be grounded in established protocol.

1. TRIAGE ASSESSMENT [Source-tagged]:
   - Category based on vitals (use standard triage: RED/YELLOW/GREEN)
   - RED FLAGS specific to this condition from reference material
   - What to communicate to the casualty medical officer (CMO)

2. MONITORING PRIORITIES [Source-tagged]:
   - What parameters, how often (e.g., "vitals q15min if unstable, q1h if stable")
   - Specific to THIS condition — what deterioration looks like
   - What to escalate immediately vs. document for rounds

3. IMMEDIATE NURSING ACTIONS [Practical Indian hospital]:
   - What's realistically available: pulse oximeter, BP cuff, thermometer, glucometer
   - IV access: what gauge, what fluid (NS/RL — what's available)
   - Positioning: specific to condition (e.g., propped up for cardiac, left lateral for liver abscess drainage)
   - What to prepare from the ward stock vs. what needs pharmacy indent

4. INVESTIGATION PREPARATION [Practical]:
   - Standard labs available in govt hospital: CBC, RFT, LFT, blood sugar, urine routine
   - What needs special request: troponin, d-dimer, ABG, blood culture
   - Imaging: X-ray (available), ultrasound (may need radiology call), CT/MRI (referral)
   - Sample collection: which tubes, timing, special handling (e.g., ABG on ice)

5. MEDICATION AWARENESS [NLEM-grounded]:
   - Only drugs commonly available in Indian govt hospitals (NLEM preferred)
   - Doses only if from reference material — otherwise "as per order"
   - Route, preparation, rate if IV
   - Contraindications the nurse must verify (allergies, pregnancy, renal function)

6. WARD WORKFLOW [Real Indian hospital]:
   - Duty handover communication (SBAR format)
   - Documentation: what to note in case sheet
   - When to call the senior resident vs. attend to yourself
   - Night duty considerations: limited staff, skeleton lab services

7. EMERGENCY PREPARATION [Condition-specific]:
   - Crash cart check: what drugs/equipment for THIS condition
   - Nearest higher center for referral if needed
   - Blood bank: crossmatch if bleeding risk"""

SENIOR_KNOWLEDGE_PROMPT = """You are building a TEACHING & DIAGNOSTIC EXPERTISE BRIEF for a senior consultant agent in an Indian medical college hospital.

{grounding_rules}

REFERENCE MATERIAL FROM MEDICAL CORPUS:
{rag_context}

CURRENT CASE:
- Diagnosis: {diagnosis}
- Specialty: {specialty}
- Difficulty: {difficulty}
- Chief complaint: {chief_complaint}
- Key differentials: {differentials}
- Learning points: {learning_points}

Create a teaching expertise brief. Every fact must be source-tagged.

1. DIAGNOSTIC ALGORITHM [Source-tagged]:
   Step-by-step reasoning path from the reference material:
   - Presenting complaint → What to consider first (life-threatening causes)
   - History clues → Which differential they support/refute
   - Examination findings → Pathognomonic signs if any
   - Investigation interpretation → Confirmatory test
   - "GOLDEN FINDING": The single most specific clue [Source: which reference case/guideline]

2. DIFFERENTIAL DIAGNOSIS MATRIX [Source-tagged]:
   From the reference material, for each major differential:
   | Differential | Supporting findings | Against | Key distinguishing test |
   ONLY include differentials mentioned in the reference material or the case data.

3. INDIAN EPIDEMIOLOGY [Source-tagged, verified only]:
   - ONLY cite statistics that are in the reference material
   - If not in reference material, use hedged language: "India has a significant burden of..."
   - Regional patterns if mentioned in corpus
   - Do NOT invent prevalence numbers

4. INDIAN GUIDELINES [Only if actually exist]:
   - Name the specific guideline document if it exists
   - If unsure whether a guideline exists, say "Per standard teaching hospital practice..."
   - Reference: API, CSI, ISCCM, INASL, ICMR — ONLY if you are certain they have guidelines for THIS condition
   - For common conditions: reference standard textbook approach (Harrison's, Sabiston, etc.)

5. NEET-PG/EXAM RELEVANCE [Verified]:
   - Classic "one-liner" descriptions (well-established ones only)
   - Question patterns: "A patient presents with X, Y, Z — diagnosis?"
   - High-yield facts from the reference material's learning points
   - ONLY include exam facts you are certain are correct

6. SOCRATIC TEACHING PLAN [Based on case data]:
   - 3 progressive questions grounded in THIS case's findings
   - Hints that point to specific findings in the case data (not generic)
   - Redirect strategies if student picks wrong differential (using case evidence)
   - Post-diagnosis teaching: pathophysiology connecting ALL findings

7. MANAGEMENT [Source-tagged, Indian context]:
   - First-line: only drugs available in NLEM or commonly stocked
   - If advanced treatment needed (e.g., PCI for STEMI): note referral requirements
   - Monitoring plan: what's realistic in a ward with 1 nurse per 20 patients
   - Disposition: admission criteria, discharge criteria, follow-up plan
   - Cost-consciousness: generic drugs, government scheme eligibility (PMJAY, etc.)"""

FAMILY_KNOWLEDGE_PROMPT = """You are building a FAMILY MEMBER PERSPECTIVE BRIEF for a clinical simulation agent in an Indian hospital.

{grounding_rules}

REFERENCE MATERIAL FROM MEDICAL CORPUS:
{rag_context}

CURRENT CASE:
- Diagnosis: {diagnosis}
- Chief complaint: {chief_complaint}
- Patient age/gender: From case data
- Location: Indian government hospital

Create a family member perspective brief. Focus on emotional and cultural context.

1. FAMILY UNDERSTANDING [Lay perspective]:
   - What the family knows about the patient's condition (in lay terms)
   - Misconceptions based on WhatsApp forwards, neighbors' advice
   - Past experiences with similar symptoms in family/community

2. EMOTIONAL STATE:
   - Anxiety level based on case severity
   - Financial worries about treatment costs
   - Work/livelihood concerns
   - Family dynamics (who's the decision maker, gender roles)

3. CULTURAL CONTEXT:
   - Home remedies already tried
   - Religious/spiritual beliefs affecting treatment
   - Dietary habits and restrictions
   - Regional customs relevant to healthcare

4. QUESTIONS & CONCERNS:
   - Cost of treatment ("kitna kharcha aayega?")
   - Duration of hospital stay
   - Who will take care of home/children
   - Whether private hospital would be better"""

LAB_TECH_KNOWLEDGE_PROMPT = """You are building a LABORATORY OPERATIONS BRIEF for a lab technician agent in an Indian government hospital.

{grounding_rules}

REFERENCE MATERIAL FROM MEDICAL CORPUS:
{rag_context}

CURRENT CASE:
- Diagnosis: {diagnosis}
- Specialty: {specialty}
- Likely investigations needed

Create a lab operations brief for realistic Indian hospital lab workflow.

1. INVESTIGATION PRIORITIES [Based on diagnosis]:
   - Which tests are most critical for this condition
   - Sample requirements and special handling
   - Turnaround times (realistic for govt hospital)

2. SAMPLE COLLECTION:
   - Proper tubes/containers for each test
   - Pre-analytical requirements (fasting, timing)
   - Common collection errors to avoid

3. LAB CONSTRAINTS [Indian govt hospital reality]:
   - Tests available in-house vs outsourced
   - Weekend/night availability limitations
   - Machine downtime issues
   - Reagent stock situations

4. RESULT INTERPRETATION HINTS:
   - Critical values to flag immediately
   - Common interferences or artifacts
   - When to suggest repeat sampling"""


# Verified Indian medical source patterns for confidence classification
VERIFIED_SOURCES = {
    "high_confidence": [
        "ICMR", "NVBDCP", "NCVBDC", "NACO", "INASL", "ISCCM", "CSI", "IAP",
        "FOGSI", "NHM", "API Guidelines", "National Snakebite Protocol",
        "RNTCP", "NTEP", "NLEM",
    ],
    "medium_confidence": [
        "JAPI", "IJMR", "Indian Heart Journal", "Indian Journal",
        "Indian J Gastroenterology", "ISG", "NDMA",
    ],
    "textbook_grade": [
        "Harrison", "Robbins", "Park", "OP Ghai", "DC Dutta",
        "Bailey", "Sabiston", "Nelson", "Schwartz",
    ],
}


def classify_source_confidence(source_str: str) -> str:
    """Classify a source string into a confidence tier.

    Returns: 'verified_guideline', 'indian_journal', 'textbook', 'corpus_case', or 'unverified'
    """
    if not source_str:
        return "unverified"
    src = source_str.upper()
    for keyword in VERIFIED_SOURCES["high_confidence"]:
        if keyword.upper() in src:
            return "verified_guideline"
    for keyword in VERIFIED_SOURCES["medium_confidence"]:
        if keyword.upper() in src:
            return "indian_journal"
    for keyword in VERIFIED_SOURCES["textbook_grade"]:
        if keyword.upper() in src:
            return "textbook"
    if "case" in source_str.lower() or "series" in source_str.lower():
        return "corpus_case"
    return "unverified"


class DynamicKnowledgeBuilder:
    """Builds role-specific medical expertise dynamically using RAG + Claude synthesis.

    Key principle: ACCURACY OVER COMPREHENSIVENESS.
    Better to say less that's correct than more that's wrong.
    Every fact must trace to: corpus, named guideline, or established textbook.
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
            role: One of 'patient', 'nurse', 'senior_doctor', 'family', 'lab_tech'

        Returns:
            Synthesized knowledge string to inject into the agent's system prompt.
        """
        case_id = case_data.get("id", "unknown")
        cache_key = (case_id, role)

        # Return cached if available
        if cache_key in self._cache:
            logger.info(f"Knowledge cache hit: {role} for case {case_id}")
            return self._cache[cache_key]

        # Step 1: Gather RAG context with source metadata
        rag_context, sources = self._gather_rag_context(case_data, role)

        # Step 2: Synthesize with Claude (strict grounding)
        knowledge = self._synthesize_knowledge(case_data, role, rag_context)

        # Step 3: Append source manifest with confidence levels
        if knowledge and sources:
            source_manifest = "\n\n=== SOURCES USED (with confidence) ===\n"
            for src in sources:
                conf = src.get("confidence", "unverified").upper()
                source_manifest += (
                    f"- [{src['case_id']}] {src['title']} "
                    f"(Source: {src['source']}) "
                    f"[{src['chunk_type']}] "
                    f"[Confidence: {conf}]\n"
                )
            source_manifest += (
                "\nNOTE: Prioritize HIGH CONFIDENCE sources. "
                "For LOW/UNVERIFIED sources, hedge your language.\n"
            )
            knowledge += source_manifest

        # Step 4: Cache and return
        if knowledge:
            self._cache[cache_key] = knowledge
            logger.info(f"Built {role} knowledge for case {case_id} ({len(knowledge)} chars, {len(sources)} sources)")

        return knowledge or ""

    def build_all_agent_knowledge(self, case_data: dict) -> dict[str, str]:
        """Build knowledge for ALL 5 agents in PARALLEL using ThreadPoolExecutor.

        This is 5x faster than sequential building since all Claude API calls run concurrently.

        Args:
            case_data: The full case dict

        Returns:
            Dict mapping role -> knowledge string for all 5 agents
        """
        start_time = time.time()
        case_id = case_data.get("id", "unknown")
        roles = ["patient", "nurse", "senior_doctor", "family", "lab_tech"]

        # Check cache first
        all_cached = True
        cached_knowledge = {}
        for role in roles:
            cache_key = (case_id, role)
            if cache_key in self._cache:
                cached_knowledge[role] = self._cache[cache_key]
            else:
                all_cached = False
                break

        if all_cached:
            logger.info(f"All agent knowledge cached for case {case_id}")
            return cached_knowledge

        logger.info(f"Building knowledge for all 5 agents in parallel for case {case_id}")

        knowledge_results = {}

        # Use ThreadPoolExecutor to run all 5 knowledge builds in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_role = {
                executor.submit(self.build_knowledge, case_data, role): role
                for role in roles
            }

            # Collect results as they complete
            for future in as_completed(future_to_role):
                role = future_to_role[future]
                try:
                    knowledge = future.result(timeout=15)  # 15 second timeout per agent (Opus adaptive is fast)
                    knowledge_results[role] = knowledge
                    logger.info(f"Completed knowledge for {role} ({len(knowledge)} chars)")
                except Exception as e:
                    logger.error(f"Failed to build knowledge for {role}: {e}")
                    # Use fallback for this role
                    knowledge_results[role] = self._fallback_knowledge(case_data, role, "")

        elapsed = time.time() - start_time
        logger.info(f"Built knowledge for all 5 agents in {elapsed:.2f}s (parallel execution)")

        return knowledge_results

    def _gather_rag_context(self, case_data: dict, role: str) -> tuple[str, list[dict]]:
        """Query RAG for role-appropriate medical knowledge.

        Returns (context_text, source_list) where source_list tracks provenance.
        """
        specialty = case_data.get("specialty", "")
        diagnosis = case_data.get("diagnosis", "")
        chief_complaint = case_data.get("chief_complaint", "")

        context_parts = []
        sources = []

        def _add_results(results: list[dict], label: str):
            if not results:
                return
            context_parts.append(f"=== {label} ===")
            for r in results:
                meta = r.get("metadata", {})
                raw_source = meta.get("source", "corpus")
                confidence = classify_source_confidence(raw_source)
                confidence_label = {
                    "verified_guideline": "HIGH CONFIDENCE - Verified Indian Guideline",
                    "indian_journal": "MEDIUM CONFIDENCE - Indian Medical Journal",
                    "textbook": "HIGH CONFIDENCE - Standard Textbook",
                    "corpus_case": "MODERATE - Corpus Case",
                    "unverified": "LOW - Unverified Source",
                }.get(confidence, "UNKNOWN")
                source_tag = f"[Source: {raw_source} | Case: {meta.get('case_id', 'unknown')} | Confidence: {confidence_label}]"
                context_parts.append(source_tag)
                context_parts.append(r["content"])
                context_parts.append("")
                sources.append({
                    "case_id": meta.get("case_id", "unknown"),
                    "title": meta.get("title", "Untitled"),
                    "source": raw_source,
                    "confidence": confidence,
                    "specialty": meta.get("specialty", ""),
                    "chunk_type": meta.get("chunk_type", ""),
                    "relevance": r.get("relevance_score", 0),
                })

        if role == "patient":
            results = self.vector_store.query(
                query_text=f"Patient presenting with {chief_complaint}. Symptoms, history for {diagnosis}",
                specialty=specialty,
                n_results=5,
                chunk_type="presentation",
            )
            _add_results(results, "SIMILAR PATIENT PRESENTATIONS FROM CORPUS")

            full_results = self.vector_store.query(
                query_text=f"Clinical case {specialty} {diagnosis}",
                specialty=specialty,
                n_results=3,
                chunk_type="full_narrative",
            )
            _add_results(full_results, "REFERENCE CASES FROM CORPUS")

        elif role == "nurse":
            results = self.vector_store.query(
                query_text=f"Clinical management {diagnosis}. Vitals monitoring nursing assessment {chief_complaint}",
                specialty=specialty,
                n_results=5,
                chunk_type="full_narrative",
            )
            _add_results(results, "CLINICAL REFERENCE FOR NURSING PROTOCOLS")

            learning_results = self.vector_store.query(
                query_text=f"Diagnosis management learning points: {diagnosis}",
                specialty=specialty,
                n_results=3,
                chunk_type="learning",
            )
            _add_results(learning_results, "DIAGNOSTIC & LEARNING MATERIAL")

        elif role == "senior_doctor":
            for chunk_type, label, n in [
                ("full_narrative", "COMPLETE CASE REFERENCES", 5),
                ("learning", "DIAGNOSTIC & TEACHING MATERIAL", 5),
                ("presentation", "CLINICAL PRESENTATIONS", 3),
            ]:
                results = self.vector_store.query(
                    query_text=f"{diagnosis} differential diagnosis pathophysiology management {specialty}",
                    specialty=specialty,
                    n_results=n,
                    chunk_type=chunk_type,
                )
                _add_results(results, f"{label} FROM CORPUS")

        elif role == "family":
            # Family needs patient experience and cultural context
            results = self.vector_store.query(
                query_text=f"Patient family perspective {chief_complaint} {diagnosis}",
                specialty=specialty,
                n_results=3,
                chunk_type="presentation",
            )
            _add_results(results, "SIMILAR PATIENT/FAMILY EXPERIENCES FROM CORPUS")

        elif role == "lab_tech":
            # Lab tech needs investigation and diagnostic info
            results = self.vector_store.query(
                query_text=f"Laboratory investigations diagnosis {diagnosis} {specialty}",
                specialty=specialty,
                n_results=5,
                chunk_type="full_narrative",
            )
            _add_results(results, "INVESTIGATION REFERENCE FROM CORPUS")

        context_text = "\n".join(context_parts) if context_parts else ""
        return context_text, sources

    def _synthesize_knowledge(
        self, case_data: dict, role: str, rag_context: str
    ) -> Optional[str]:
        """Use Claude Opus with extended thinking to synthesize role-specific expertise.

        The grounding rules ensure Claude only states verifiable facts.
        """
        if not self.client:
            logger.warning("No Claude client — returning structured RAG context")
            return self._fallback_knowledge(case_data, role, rag_context)

        prompts = {
            "patient": PATIENT_KNOWLEDGE_PROMPT,
            "nurse": NURSE_KNOWLEDGE_PROMPT,
            "senior_doctor": SENIOR_KNOWLEDGE_PROMPT,
            "family": FAMILY_KNOWLEDGE_PROMPT,
            "lab_tech": LAB_TECH_KNOWLEDGE_PROMPT,
        }
        prompt_template = prompts.get(role)
        if not prompt_template:
            logger.warning(f"No prompt template for role: {role}")
            return self._fallback_knowledge(case_data, role, rag_context)

        vitals = case_data.get("vital_signs", {})

        # Build prompt with grounding rules + RAG context
        prompt = prompt_template.format(
            grounding_rules=SOURCE_GROUNDING_RULES,
            rag_context=rag_context or "NO REFERENCE MATERIAL AVAILABLE. Use ONLY well-established textbook facts. Tag everything [Textbook] and be conservative.",
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
                temperature=1,  # Required to be 1 for adaptive thinking
                thinking={
                    "type": "adaptive",  # Use adaptive thinking for better performance
                },
                messages=[{"role": "user", "content": prompt}],
            )

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
        """Fallback when Claude is unavailable — return structured RAG context with source tags.

        This is a conservative fallback: only raw corpus data, no synthesis.
        """
        diagnosis = case_data.get("diagnosis", "")
        specialty = case_data.get("specialty", "")
        chief_complaint = case_data.get("chief_complaint", "")

        header = (
            "NOTE: Dynamic knowledge synthesis unavailable. Using RAG corpus directly.\n"
            "ONLY use facts from the reference material below. Do NOT invent or assume.\n\n"
        )

        if role == "patient":
            return (
                f"{header}"
                f"CONDITION: {chief_complaint} ({specialty})\n"
                f"Describe symptoms based ONLY on the presentation data provided to you.\n"
                f"If asked something not in your case data, say 'pata nahi doctor'.\n\n"
                f"REFERENCE MATERIAL [Corpus]:\n{rag_context[:2000]}"
            )

        if role == "nurse":
            vitals = case_data.get("vital_signs", {})
            return (
                f"{header}"
                f"PATIENT: {chief_complaint} ({specialty})\n"
                f"VITALS: BP {vitals.get('bp')}, HR {vitals.get('hr')}, "
                f"RR {vitals.get('rr')}, SpO2 {vitals.get('spo2')}%\n"
                f"Report only what you observe. For protocols, say 'as per hospital protocol'.\n\n"
                f"REFERENCE MATERIAL [Corpus]:\n{rag_context[:2000]}"
            )

        if role == "senior_doctor":
            return (
                f"{header}"
                f"CASE: {chief_complaint} ({specialty})\n"
                f"DIAGNOSIS: {diagnosis}\n"
                f"DIFFERENTIALS: {', '.join(case_data.get('differentials', []))}\n"
                f"LEARNING POINTS: {'; '.join(case_data.get('learning_points', []))}\n"
                f"Teach using Socratic method. Only reference facts from the case data or reference material.\n\n"
                f"REFERENCE MATERIAL [Corpus]:\n{rag_context[:3000]}"
            )

        if role == "family":
            return (
                f"{header}"
                f"PATIENT CONDITION: {chief_complaint}\n"
                f"You are a worried family member. Express concern in Hinglish.\n"
                f"Share what home remedies you tried, cost concerns, work worries.\n"
                f"Only describe what a family member would know in lay terms.\n\n"
                f"REFERENCE MATERIAL [Corpus]:\n{rag_context[:1500]}"
            )

        if role == "lab_tech":
            return (
                f"{header}"
                f"CASE: {chief_complaint} ({specialty})\n"
                f"Focus on sample collection, turnaround times, and result reporting.\n"
                f"Mention realistic govt hospital lab constraints.\n"
                f"Use technical terms for tests but explain in simple terms to students.\n\n"
                f"REFERENCE MATERIAL [Corpus]:\n{rag_context[:1500]}"
            )

        return f"{header}{rag_context[:2000]}" if rag_context else header


# Singleton instance
knowledge_builder = DynamicKnowledgeBuilder()
