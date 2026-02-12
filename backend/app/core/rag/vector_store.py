"""ChromaDB vector store for medical case corpus."""

import os
import json
import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

CORPUS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "medical_corpus"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "vector_db"

COLLECTION_NAME = "medical_cases"


class MedicalVectorStore:
    """Manages ChromaDB vector store for medical case embeddings."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("CHROMA_DB_PATH", str(DEFAULT_DB_PATH))
        Path(self.db_path).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB initialized at {self.db_path}, collection has {self.collection.count()} documents")

    def ingest_corpus(self, corpus_dir: Optional[str] = None) -> int:
        """Load all JSON case files from corpus directory, chunk, and embed into ChromaDB."""
        corpus_path = Path(corpus_dir) if corpus_dir else CORPUS_DIR
        if not corpus_path.exists():
            logger.warning(f"Corpus directory not found: {corpus_path}")
            return 0

        total_added = 0
        for json_file in sorted(corpus_path.glob("*.json")):
            try:
                with open(json_file, "r") as f:
                    cases = json.load(f)
                added = self._ingest_cases(cases)
                total_added += added
                logger.info(f"Ingested {added} chunks from {json_file.name}")
            except Exception as e:
                logger.error(f"Error ingesting {json_file.name}: {e}")

        logger.info(f"Total documents in collection: {self.collection.count()}")
        return total_added

    def _ingest_cases(self, cases: list[dict]) -> int:
        """Convert structured cases into text chunks and add to ChromaDB."""
        ids = []
        documents = []
        metadatas = []

        for case in cases:
            case_id = case.get("id", "UNKNOWN")

            # Skip if already in collection
            existing = self.collection.get(ids=[f"{case_id}_full"])
            if existing and existing["ids"]:
                continue

            # Chunk 1: Full case narrative (primary retrieval document)
            full_text = self._case_to_narrative(case)
            ids.append(f"{case_id}_full")
            documents.append(full_text)
            metadatas.append({
                "case_id": case_id,
                "specialty": case.get("specialty", ""),
                "difficulty": case.get("difficulty", ""),
                "chunk_type": "full_narrative",
                "title": case.get("title", ""),
                "source": case.get("source", ""),
            })

            # Chunk 2: Clinical presentation (for symptom-based retrieval)
            presentation_text = self._case_to_presentation(case)
            ids.append(f"{case_id}_presentation")
            documents.append(presentation_text)
            metadatas.append({
                "case_id": case_id,
                "specialty": case.get("specialty", ""),
                "difficulty": case.get("difficulty", ""),
                "chunk_type": "presentation",
                "title": case.get("title", ""),
            })

            # Chunk 3: Diagnosis and learning points (for educational retrieval)
            learning_text = self._case_to_learning(case)
            ids.append(f"{case_id}_learning")
            documents.append(learning_text)
            metadatas.append({
                "case_id": case_id,
                "specialty": case.get("specialty", ""),
                "difficulty": case.get("difficulty", ""),
                "chunk_type": "learning",
                "title": case.get("title", ""),
            })

        if ids:
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

        return len(ids)

    def _case_to_narrative(self, case: dict) -> str:
        """Convert a structured case to a full narrative text chunk for embedding."""
        parts = [
            f"Clinical Case: {case.get('title', 'Untitled')}",
            f"Specialty: {case.get('specialty', '')} | Difficulty: {case.get('difficulty', '')}",
            f"Source: {case.get('source', '')}",
        ]

        demographics = case.get("demographics", {})
        if demographics:
            parts.append(f"Patient: {demographics.get('age', '')} year old {demographics.get('gender', '')} from {demographics.get('location', '')}")

        for field in ["chief_complaint", "presentation", "history", "physical_exam", "investigations"]:
            if case.get(field):
                label = field.replace("_", " ").title()
                parts.append(f"{label}: {case[field]}")

        if case.get("vital_signs"):
            vs = case["vital_signs"]
            parts.append(f"Vital Signs: BP {vs.get('bp', 'N/A')}, HR {vs.get('hr', 'N/A')}, RR {vs.get('rr', 'N/A')}, Temp {vs.get('temp', 'N/A')}°C, SpO2 {vs.get('spo2', 'N/A')}%")

        parts.append(f"Diagnosis: {case.get('diagnosis', '')}")

        if case.get("differentials"):
            parts.append(f"Differential Diagnoses: {', '.join(case['differentials'])}")

        if case.get("learning_points"):
            parts.append("Key Learning Points: " + " | ".join(case["learning_points"]))

        if case.get("india_context"):
            parts.append(f"Indian Context: {case['india_context']}")

        return "\n\n".join(parts)

    def _case_to_presentation(self, case: dict) -> str:
        """Extract presentation-focused chunk for symptom-based retrieval."""
        parts = [
            f"Patient Presentation: {case.get('title', '')}",
        ]
        demographics = case.get("demographics", {})
        if demographics:
            parts.append(f"{demographics.get('age', '')} year old {demographics.get('gender', '')} from {demographics.get('location', '')}")

        parts.append(f"Chief Complaint: {case.get('chief_complaint', '')}")
        parts.append(f"Presentation: {case.get('presentation', '')}")

        if case.get("vital_signs"):
            vs = case["vital_signs"]
            parts.append(f"Vital Signs: BP {vs.get('bp', 'N/A')}, HR {vs.get('hr', 'N/A')}, RR {vs.get('rr', 'N/A')}, Temp {vs.get('temp', 'N/A')}°C, SpO2 {vs.get('spo2', 'N/A')}%")

        parts.append(f"History: {case.get('history', '')}")
        parts.append(f"Physical Examination: {case.get('physical_exam', '')}")

        return "\n\n".join(parts)

    def _case_to_learning(self, case: dict) -> str:
        """Extract learning-focused chunk for educational retrieval."""
        parts = [
            f"Diagnosis and Teaching Points: {case.get('title', '')}",
            f"Specialty: {case.get('specialty', '')}",
            f"Final Diagnosis: {case.get('diagnosis', '')}",
        ]

        if case.get("differentials"):
            parts.append(f"Differential Diagnoses: {', '.join(case['differentials'])}")

        if case.get("learning_points"):
            parts.append("Learning Points:")
            for i, point in enumerate(case["learning_points"], 1):
                parts.append(f"  {i}. {point}")

        if case.get("atypical_features"):
            parts.append(f"Atypical Features: {case['atypical_features']}")

        if case.get("india_context"):
            parts.append(f"Indian Context: {case['india_context']}")

        return "\n\n".join(parts)

    def query(
        self,
        query_text: str,
        specialty: Optional[str] = None,
        difficulty: Optional[str] = None,
        n_results: int = 5,
        chunk_type: Optional[str] = None,
    ) -> list[dict]:
        """Query the vector store for relevant medical cases."""
        where_filter = {}
        conditions = []

        if specialty:
            conditions.append({"specialty": specialty})
        if difficulty:
            conditions.append({"difficulty": difficulty})
        if chunk_type:
            conditions.append({"chunk_type": chunk_type})

        if len(conditions) > 1:
            where_filter = {"$and": conditions}
        elif len(conditions) == 1:
            where_filter = conditions[0]

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results, self.collection.count() or 1),
                where=where_filter if where_filter else None,
            )
        except Exception as e:
            logger.error(f"ChromaDB query error: {e}")
            return []

        documents = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else None
                documents.append({
                    "content": doc,
                    "metadata": metadata,
                    "relevance_score": 1 - (distance or 0),  # Convert distance to similarity
                })

        return documents

    def get_case_by_id(self, case_id: str) -> Optional[dict]:
        """Retrieve a specific case by its ID."""
        try:
            result = self.collection.get(ids=[f"{case_id}_full"])
            if result and result["documents"]:
                return {
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                }
        except Exception:
            pass
        return None

    def get_specialties(self) -> list[str]:
        """Get list of unique specialties in the corpus."""
        try:
            result = self.collection.get(where={"chunk_type": "full_narrative"})
            if result and result["metadatas"]:
                return sorted(set(m.get("specialty", "") for m in result["metadatas"] if m.get("specialty")))
        except Exception:
            pass
        return []

    def count(self) -> int:
        """Get total number of documents in the collection."""
        return self.collection.count()

    def reset(self):
        """Delete and recreate the collection."""
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Vector store reset complete")
