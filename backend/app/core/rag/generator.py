"""RAG-powered clinical case generator using ChromaDB + Claude API."""

import json
import logging
import os
import uuid
from typing import Optional
from pathlib import Path
from datetime import datetime

import anthropic

from app.core.rag.vector_store import MedicalVectorStore
from app.core.rag.retriever import MedicalRetriever

logger = logging.getLogger(__name__)

# Claude API case generation prompt
CASE_GENERATION_PROMPT = """You are an expert medical case writer for Clinical-Mind, an AI-powered clinical reasoning simulator for Indian medical students (MBBS final year, interns, NEET-PG aspirants).

Using the reference cases from the medical corpus below as inspiration and factual grounding, generate a UNIQUE, ORIGINAL clinical case that:

1. Is set in an Indian healthcare context (Indian demographics, locations, disease patterns, healthcare system)
2. Matches the requested specialty and difficulty level
3. Has realistic, medically accurate clinical details
4. Includes atypical or challenging features appropriate to the difficulty level
5. Tests clinical reasoning, not just knowledge recall

IMPORTANT RULES:
- Do NOT copy any reference case verbatim. Use them only as factual grounding.
- Create a completely new patient scenario with different demographics, presentation nuances, and clinical twists.
- For "beginner" cases: straightforward presentation, classic findings
- For "intermediate" cases: some atypical features, requires careful analysis
- For "advanced" cases: atypical presentation, multiple co-morbidities, diagnostic dilemmas

{rag_context}

Generate a case for:
- Specialty: {specialty}
- Difficulty: {difficulty}
- Student Level: {year_level}

Respond with ONLY a valid JSON object (no markdown, no explanation) with this exact structure:
{{
  "patient": {{"age": <int>, "gender": "<Male/Female>", "location": "<Indian city, state>"}},
  "chief_complaint": "<brief chief complaint>",
  "initial_presentation": "<2-3 sentence clinical vignette presented to the student>",
  "vital_signs": {{"bp": "<systolic/diastolic>", "hr": <int>, "rr": <int>, "temp": <float>, "spo2": <int>}},
  "stages": [
    {{"stage": "history", "info": "<detailed history findings revealed when student takes history>"}},
    {{"stage": "physical_exam", "info": "<detailed physical exam findings>"}},
    {{"stage": "labs", "info": "<investigation results including labs, imaging, special tests>"}}
  ],
  "diagnosis": "<correct final diagnosis>",
  "differentials": ["<differential 1>", "<differential 2>", "<differential 3>", "<differential 4>", "<differential 5>"],
  "learning_points": ["<point 1>", "<point 2>", "<point 3>", "<point 4>"],
  "atypical_features": "<what makes this case challenging or unique>",
  "specialty": "{specialty}",
  "difficulty": "{difficulty}"
}}"""

EVALUATION_PROMPT = """You are a clinical reasoning evaluator for medical students. A student has submitted a diagnosis for a clinical case.

{rag_context}

Case Diagnosis: {correct_diagnosis}
Student's Diagnosis: {student_diagnosis}
Student's Reasoning: {student_reasoning}

Evaluate the student's diagnosis and reasoning. Consider:
1. Is the diagnosis correct or partially correct?
2. What was good about their clinical reasoning?
3. What did they miss or get wrong?
4. What are the key learning points?

Respond with ONLY a valid JSON object:
{{
  "is_correct": <true/false>,
  "accuracy_score": <0-100>,
  "feedback": "<2-3 sentences of constructive feedback>",
  "reasoning_strengths": ["<strength 1>", "<strength 2>"],
  "reasoning_gaps": ["<gap 1>", "<gap 2>"],
  "learning_points": ["<point 1>", "<point 2>", "<point 3>"],
  "suggested_review_topics": ["<topic 1>", "<topic 2>"]
}}"""


class CaseGenerator:
    """RAG-powered clinical case generator using ChromaDB + Claude API."""

    def __init__(self, vector_store: Optional[MedicalVectorStore] = None):
        # Create persistent storage directory
        self.storage_dir = Path("./data/active_cases")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Load persisted cases on startup
        self.active_cases: dict = self._load_persisted_cases()
        logger.info(f"Loaded {len(self.active_cases)} persisted cases from disk")

        # Initialize vector store and retriever
        if vector_store:
            self.vector_store = vector_store
        else:
            self.vector_store = MedicalVectorStore()
        self.retriever = MedicalRetriever(self.vector_store)

        # Initialize Claude client
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.client = None
        if self.api_key and self.api_key != "sk-ant-your-key-here":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Claude API client initialized")
            except Exception as e:
                logger.warning(f"Claude API client init failed: {e}")

        # Auto-ingest corpus if vector store is empty
        if self.vector_store.count() == 0:
            logger.info("Vector store empty, ingesting seed corpus...")
            count = self.vector_store.ingest_corpus()
            logger.info(f"Ingested {count} document chunks into ChromaDB")

    def generate_case(
        self,
        specialty: str,
        difficulty: str = "intermediate",
        year_level: str = "final_year",
    ) -> dict:
        """Generate a unique clinical case using RAG context + Claude API."""
        case_id = str(uuid.uuid4())[:8]

        # Step 1: Retrieve relevant context from ChromaDB
        rag_context = self.retriever.retrieve_case_context(
            specialty=specialty,
            difficulty=difficulty,
            n_results=5,
        )

        # Step 2: Generate case via Claude API (or fallback to RAG-only)
        case_data = None
        if self.client and rag_context:
            case_data = self._generate_with_claude(
                specialty=specialty,
                difficulty=difficulty,
                year_level=year_level,
                rag_context=rag_context,
            )

        # Step 3: Fallback to corpus-based case if Claude unavailable
        if not case_data:
            case_data = self._fallback_from_corpus(specialty, difficulty)

        case_data["id"] = case_id
        self.active_cases[case_id] = case_data

        # Save to persistent storage
        self._save_case_to_disk(case_id, case_data)

        # Clean up old cases periodically
        if len(self.active_cases) > 20:  # Cleanup when we have many cases
            self._cleanup_old_cases()

        return case_data

    def _generate_with_claude(
        self,
        specialty: str,
        difficulty: str,
        year_level: str,
        rag_context: str,
    ) -> Optional[dict]:
        """Generate a case using Claude API with RAG context."""
        prompt = CASE_GENERATION_PROMPT.format(
            rag_context=rag_context,
            specialty=specialty,
            difficulty=difficulty,
            year_level=year_level,
        )

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()

            # Parse JSON from response (handle potential markdown wrapping)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            case_data = json.loads(response_text)
            logger.info(f"Claude generated case: {case_data.get('diagnosis', 'unknown')}")
            return case_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
        except Exception as e:
            logger.error(f"Case generation error: {e}")

        return None

    def _fallback_from_corpus(self, specialty: str, difficulty: str) -> dict:
        """Fallback: return a case directly from the corpus when Claude API is unavailable."""
        results = self.vector_store.query(
            query_text=f"Clinical case {specialty} {difficulty}",
            specialty=specialty,
            difficulty=difficulty,
            n_results=1,
            chunk_type="full_narrative",
        )

        if results:
            # Try to find the original JSON case data
            case_id = results[0]["metadata"].get("case_id", "")
            case_data = self._load_case_from_corpus(case_id, specialty)
            if case_data:
                return case_data

        # Ultimate fallback: return a minimal case from RAG text
        if results:
            return {
                "patient": {"age": 35, "gender": "Male", "location": "India"},
                "chief_complaint": results[0]["metadata"].get("title", "Medical case"),
                "initial_presentation": results[0]["content"][:500],
                "vital_signs": {"bp": "120/80", "hr": 80, "rr": 16, "temp": 37.0, "spo2": 98},
                "stages": [
                    {"stage": "history", "info": "Please configure ANTHROPIC_API_KEY for dynamic case generation. Currently serving from corpus."},
                    {"stage": "physical_exam", "info": "Physical examination findings from corpus."},
                    {"stage": "labs", "info": "Laboratory results from corpus."},
                ],
                "diagnosis": "Configure API key for full case generation",
                "differentials": [],
                "learning_points": ["Set ANTHROPIC_API_KEY environment variable to enable AI-powered case generation"],
                "atypical_features": "",
                "specialty": specialty,
                "difficulty": difficulty,
            }

        # Absolute fallback if nothing in corpus
        return self._empty_case(specialty, difficulty)

    def _load_case_from_corpus(self, case_id: str, specialty: str) -> Optional[dict]:
        """Load the original structured case from corpus JSON files."""
        from app.core.rag.vector_store import CORPUS_DIR
        import json

        for json_file in CORPUS_DIR.glob("*.json"):
            try:
                with open(json_file) as f:
                    cases = json.load(f)
                for case in cases:
                    if case.get("id") == case_id:
                        # Transform to API format
                        return {
                            "patient": case.get("demographics", {"age": 35, "gender": "Unknown", "location": "India"}),
                            "chief_complaint": case.get("chief_complaint", ""),
                            "initial_presentation": case.get("presentation", ""),
                            "vital_signs": case.get("vital_signs", {}),
                            "stages": case.get("stages", [
                                {"stage": "history", "info": case.get("history", "")},
                                {"stage": "physical_exam", "info": case.get("physical_exam", "")},
                                {"stage": "labs", "info": case.get("investigations", "")},
                            ]),
                            "diagnosis": case.get("diagnosis", ""),
                            "differentials": case.get("differentials", []),
                            "learning_points": case.get("learning_points", []),
                            "atypical_features": case.get("atypical_features", ""),
                            "specialty": case.get("specialty", specialty),
                            "difficulty": case.get("difficulty", "intermediate"),
                        }
            except Exception:
                continue
        return None

    def _empty_case(self, specialty: str, difficulty: str) -> dict:
        """Return a placeholder case when corpus is empty."""
        return {
            "patient": {"age": 0, "gender": "Unknown", "location": "India"},
            "chief_complaint": "No cases available",
            "initial_presentation": "Please run the corpus ingestion script to load medical cases into the RAG system.",
            "vital_signs": {"bp": "N/A", "hr": 0, "rr": 0, "temp": 0, "spo2": 0},
            "stages": [],
            "diagnosis": "Corpus empty",
            "differentials": [],
            "learning_points": ["Run: python -m scripts.ingest to load the medical corpus"],
            "specialty": specialty,
            "difficulty": difficulty,
        }

    def get_case(self, case_id: str) -> Optional[dict]:
        # First check in-memory cache
        case = self.active_cases.get(case_id)
        if case:
            return case

        # If not in memory, try loading from disk
        case_file = self.storage_dir / f"{case_id}.json"
        if case_file.exists():
            try:
                with open(case_file, 'r') as f:
                    data = json.load(f)
                    case_data = data.get("case_data")
                    if case_data:
                        # Cache it in memory for future use
                        self.active_cases[case_id] = case_data
                        logger.info(f"Loaded case {case_id} from disk cache")
                        return case_data
            except Exception as e:
                logger.error(f"Failed to load case {case_id} from disk: {e}")

        return None

    def process_action(self, case_id: str, action_type: str, student_input: Optional[str] = None) -> dict:
        case = self.active_cases.get(case_id)
        if not case:
            return {"error": "Case not found"}

        stage_map = {
            "take_history": 0,
            "physical_exam": 1,
            "order_labs": 2,
        }

        stage_index = stage_map.get(action_type)
        if stage_index is not None and stage_index < len(case.get("stages", [])):
            return {
                "action": action_type,
                "result": case["stages"][stage_index],
            }

        return {"action": action_type, "result": "Action processed"}

    def evaluate_diagnosis(self, case_id: str, diagnosis: str, reasoning: str = "") -> dict:
        """Evaluate student diagnosis using RAG context + Claude API for rich feedback."""
        case = self.active_cases.get(case_id)
        if not case:
            return {"error": "Case not found"}

        correct_diagnosis = case.get("diagnosis", "")

        # Try Claude API evaluation with RAG context
        if self.client:
            evaluation = self._evaluate_with_claude(
                correct_diagnosis=correct_diagnosis,
                student_diagnosis=diagnosis,
                student_reasoning=reasoning,
                specialty=case.get("specialty", ""),
            )
            if evaluation:
                evaluation["correct_diagnosis"] = correct_diagnosis
                evaluation["student_diagnosis"] = diagnosis
                evaluation["differentials"] = case.get("differentials", [])
                return evaluation

        # Fallback: keyword-based matching
        is_correct = any(
            keyword in diagnosis.lower()
            for keyword in correct_diagnosis.lower().split()
            if len(keyword) > 3
        )

        return {
            "student_diagnosis": diagnosis,
            "correct_diagnosis": correct_diagnosis,
            "is_correct": is_correct,
            "accuracy_score": 100 if is_correct else 30,
            "differentials": case.get("differentials", []),
            "learning_points": case.get("learning_points", []),
            "feedback": "Excellent clinical reasoning!" if is_correct else f"The correct diagnosis is {correct_diagnosis}. Review the key learning points.",
            "reasoning_strengths": [],
            "reasoning_gaps": [],
            "suggested_review_topics": [],
        }

    def _evaluate_with_claude(
        self,
        correct_diagnosis: str,
        student_diagnosis: str,
        student_reasoning: str,
        specialty: str,
    ) -> Optional[dict]:
        """Use Claude API to provide rich evaluation feedback."""
        rag_context = self.retriever.retrieve_for_evaluation(
            diagnosis=correct_diagnosis,
            specialty=specialty,
        )

        prompt = EVALUATION_PROMPT.format(
            rag_context=rag_context,
            correct_diagnosis=correct_diagnosis,
            student_diagnosis=student_diagnosis,
            student_reasoning=student_reasoning or "No reasoning provided",
        )

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            return json.loads(response_text)

        except Exception as e:
            logger.error(f"Claude evaluation error: {e}")
            return None

    def get_corpus_stats(self) -> dict:
        """Get statistics about the loaded RAG corpus."""
        return self.retriever.get_corpus_stats()

    def _save_case_to_disk(self, case_id: str, case_data: dict):
        """Save a case to persistent storage."""
        try:
            case_file = self.storage_dir / f"{case_id}.json"
            with open(case_file, 'w') as f:
                json.dump({
                    "case_id": case_id,
                    "case_data": case_data,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
            logger.info(f"Saved case {case_id} to disk")
        except Exception as e:
            logger.error(f"Failed to save case {case_id} to disk: {e}")

    def _load_persisted_cases(self) -> dict:
        """Load all persisted cases from disk."""
        cases = {}
        try:
            for case_file in self.storage_dir.glob("*.json"):
                with open(case_file, 'r') as f:
                    data = json.load(f)
                    case_id = data.get("case_id")
                    case_data = data.get("case_data")
                    if case_id and case_data:
                        cases[case_id] = case_data
                        logger.debug(f"Loaded case {case_id} from disk")
        except Exception as e:
            logger.error(f"Failed to load persisted cases: {e}")
        return cases

    def _cleanup_old_cases(self):
        """Clean up cases older than 24 hours."""
        try:
            cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)  # 24 hours ago
            for case_file in self.storage_dir.glob("*.json"):
                if case_file.stat().st_mtime < cutoff_time:
                    case_file.unlink()
                    logger.debug(f"Cleaned up old case file: {case_file.name}")
        except Exception as e:
            logger.error(f"Failed to cleanup old cases: {e}")
