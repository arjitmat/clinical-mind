"""RAG retriever - queries ChromaDB and formats context for Claude API."""

import logging
from typing import Optional

from app.core.rag.vector_store import MedicalVectorStore

logger = logging.getLogger(__name__)


class MedicalRetriever:
    """Retrieves relevant medical case context from the vector store for case generation."""

    def __init__(self, vector_store: MedicalVectorStore):
        self.vector_store = vector_store

    def retrieve_case_context(
        self,
        specialty: str,
        difficulty: str = "intermediate",
        topic_hint: Optional[str] = None,
        n_results: int = 5,
    ) -> str:
        """Retrieve relevant case context for generating a new clinical case.

        Returns formatted context string suitable for injection into Claude prompt.
        """
        # Build a query that targets the specialty and difficulty
        query = f"Clinical case in {specialty} for medical students, {difficulty} difficulty level"
        if topic_hint:
            query += f", related to {topic_hint}"

        # Get full narrative cases as primary context
        results = self.vector_store.query(
            query_text=query,
            specialty=specialty,
            n_results=n_results,
            chunk_type="full_narrative",
        )

        if not results:
            # Fallback: try without specialty filter
            results = self.vector_store.query(
                query_text=query,
                n_results=n_results,
                chunk_type="full_narrative",
            )

        if not results:
            logger.warning(f"No RAG context found for specialty={specialty}, difficulty={difficulty}")
            return ""

        # Format context for Claude
        context_parts = [
            "=== REFERENCE MEDICAL CASES FROM CORPUS ===",
            f"Specialty: {specialty} | Difficulty: {difficulty}",
            f"Retrieved {len(results)} reference cases for inspiration.",
            "",
        ]

        for i, result in enumerate(results, 1):
            context_parts.append(f"--- Reference Case {i} (Relevance: {result['relevance_score']:.2f}) ---")
            context_parts.append(result["content"])
            context_parts.append("")

        context_parts.append("=== END OF REFERENCE CASES ===")

        return "\n".join(context_parts)

    def retrieve_for_evaluation(
        self,
        diagnosis: str,
        specialty: str,
    ) -> str:
        """Retrieve context relevant to a specific diagnosis for evaluating student answers."""
        query = f"Diagnosis: {diagnosis}. Clinical features, differentials, and learning points."

        results = self.vector_store.query(
            query_text=query,
            specialty=specialty,
            n_results=3,
            chunk_type="learning",
        )

        if not results:
            results = self.vector_store.query(
                query_text=query,
                n_results=3,
                chunk_type="learning",
            )

        if not results:
            return ""

        context_parts = ["=== REFERENCE LEARNING MATERIAL ==="]
        for result in results:
            context_parts.append(result["content"])
            context_parts.append("")
        context_parts.append("=== END REFERENCE ===")

        return "\n".join(context_parts)

    def retrieve_similar_cases(
        self,
        presentation: str,
        n_results: int = 3,
    ) -> list[dict]:
        """Find cases similar to a given presentation text."""
        results = self.vector_store.query(
            query_text=presentation,
            n_results=n_results,
            chunk_type="presentation",
        )
        return results

    def get_corpus_stats(self) -> dict:
        """Get statistics about the loaded corpus."""
        total = self.vector_store.count()
        specialties = self.vector_store.get_specialties()
        return {
            "total_documents": total,
            "total_cases": total // 3,  # 3 chunks per case
            "specialties": specialties,
            "status": "loaded" if total > 0 else "empty",
        }
