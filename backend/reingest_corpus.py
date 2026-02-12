#!/usr/bin/env python3
"""
Script to reingest the entire medical corpus into ChromaDB vector store.
This will reset the vector store and load all cases from the corpus files.
"""
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.core.rag.vector_store import MedicalVectorStore

def main():
    print("=" * 60)
    print("Clinical-Mind RAG Corpus Reingestion")
    print("=" * 60)

    # Initialize vector store
    print("\n[1/3] Initializing vector store...")
    store = MedicalVectorStore()
    current_count = store.count()
    print(f"Current documents in ChromaDB: {current_count}")

    # Reset the vector store
    print("\n[2/3] Resetting vector store (deleting all existing documents)...")
    store.reset()
    print("Vector store reset complete.")

    # Reingest the entire corpus
    print("\n[3/3] Ingesting medical corpus from JSON files...")
    count = store.ingest_corpus()

    # Get final statistics
    final_count = store.count()
    specialties = store.get_specialties()

    print("\n" + "=" * 60)
    print("Reingestion Complete!")
    print("=" * 60)
    print(f"Total document chunks ingested: {final_count}")
    print(f"Total unique cases: {final_count // 3}")  # 3 chunks per case
    print(f"Specialties covered: {len(specialties)}")
    print(f"Specialty list: {', '.join(specialties)}")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
