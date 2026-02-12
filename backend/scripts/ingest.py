#!/usr/bin/env python3
"""CLI script to ingest medical corpus into ChromaDB vector store.

Usage:
    # Ingest seed corpus (JSON files from data/medical_corpus/)
    python -m scripts.ingest

    # Ingest with reset (clear existing data first)
    python -m scripts.ingest --reset

    # Scrape from a specific source
    python -m scripts.ingest --scrape japi

    # Ingest a PDF file
    python -m scripts.ingest --pdf /path/to/textbook.pdf

    # Show corpus statistics
    python -m scripts.ingest --stats
"""

import argparse
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.rag.vector_store import MedicalVectorStore
from app.core.rag.retriever import MedicalRetriever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("ingest")


def main():
    parser = argparse.ArgumentParser(description="Clinical-Mind RAG Corpus Ingestion")
    parser.add_argument("--reset", action="store_true", help="Reset vector store before ingesting")
    parser.add_argument("--stats", action="store_true", help="Show corpus statistics")
    parser.add_argument("--scrape", type=str, help="Scrape source (japi, ijmr, ijem)")
    parser.add_argument("--pdf", type=str, help="Ingest a PDF file")
    parser.add_argument("--corpus-dir", type=str, help="Custom corpus directory path")
    parser.add_argument("--query", type=str, help="Test query against the vector store")
    parser.add_argument("--specialty", type=str, help="Filter by specialty (for query)")
    args = parser.parse_args()

    store = MedicalVectorStore()
    retriever = MedicalRetriever(store)

    if args.stats:
        stats = retriever.get_corpus_stats()
        print("\n=== Clinical-Mind RAG Corpus Statistics ===")
        print(f"  Total documents:  {stats['total_documents']}")
        print(f"  Total cases:      {stats['total_cases']}")
        print(f"  Specialties:      {', '.join(stats['specialties'])}")
        print(f"  Status:           {stats['status']}")
        print()
        return

    if args.reset:
        logger.info("Resetting vector store...")
        store.reset()
        logger.info("Vector store cleared")

    if args.scrape:
        from app.core.rag.scraper import MedicalCorpusScraper

        scraper = MedicalCorpusScraper()
        logger.info(f"Scraping from: {args.scrape}")
        cases = scraper.scrape_source(args.scrape)
        if cases:
            scraper.save_scraped_cases(cases, f"{args.scrape}_scraped.json")
            # Re-ingest all corpus (includes newly scraped)
            count = store.ingest_corpus()
            logger.info(f"Ingested {count} total chunks")
        else:
            logger.warning("No cases scraped. Check source URL and network connectivity.")
        return

    if args.pdf:
        from app.core.rag.scraper import MedicalCorpusScraper

        scraper = MedicalCorpusScraper()
        logger.info(f"Processing PDF: {args.pdf}")
        cases = scraper.ingest_pdf(args.pdf)
        if cases:
            pdf_name = Path(args.pdf).stem
            scraper.save_scraped_cases(cases, f"pdf_{pdf_name}.json")
            count = store.ingest_corpus()
            logger.info(f"Ingested {count} total chunks")
        else:
            logger.warning("No cases extracted from PDF.")
        return

    if args.query:
        logger.info(f"Querying: '{args.query}'")
        results = store.query(
            query_text=args.query,
            specialty=args.specialty,
            n_results=3,
        )
        print(f"\n=== Query Results ({len(results)} found) ===\n")
        for i, r in enumerate(results, 1):
            print(f"--- Result {i} (score: {r['relevance_score']:.3f}) ---")
            print(f"  Title:     {r['metadata'].get('title', 'N/A')}")
            print(f"  Specialty: {r['metadata'].get('specialty', 'N/A')}")
            print(f"  Type:      {r['metadata'].get('chunk_type', 'N/A')}")
            print(f"  Preview:   {r['content'][:200]}...")
            print()
        return

    # Default: ingest seed corpus
    logger.info("Ingesting seed medical corpus into ChromaDB...")
    corpus_dir = args.corpus_dir if args.corpus_dir else None
    count = store.ingest_corpus(corpus_dir)
    logger.info(f"Done! Ingested {count} document chunks")

    # Show stats
    stats = retriever.get_corpus_stats()
    print(f"\n=== Ingestion Complete ===")
    print(f"  Documents: {stats['total_documents']}")
    print(f"  Cases:     {stats['total_cases']}")
    print(f"  Specialties: {', '.join(stats['specialties'])}")
    print()


if __name__ == "__main__":
    main()
