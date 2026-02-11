"""Web scraper for medical corpus sources - JAPI, IJMR, and other open-access journals."""

import json
import logging
import re
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CORPUS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "medical_corpus"

# Configurable source URLs
SOURCES = {
    "japi": {
        "name": "Journal of the Association of Physicians of India",
        "base_url": "https://www.japi.org",
        "archive_path": "/past-issues",
        "article_selector": "div.article-list a",
        "content_selector": "div.article-content",
    },
    "ijmr": {
        "name": "Indian Journal of Medical Research",
        "base_url": "https://journals.lww.com/ijmr",
        "archive_path": "/currentissue",
        "article_selector": "div.article-list a",
        "content_selector": "div.ejp-article-text",
    },
    "ijem": {
        "name": "Indian Journal of Endocrinology and Metabolism",
        "base_url": "https://journals.lww.com/indjem",
        "archive_path": "/currentissue",
        "article_selector": "div.article-list a",
        "content_selector": "div.ejp-article-text",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Clinical-Mind Research Bot; Educational Use)",
    "Accept": "text/html,application/xhtml+xml",
}


class MedicalCorpusScraper:
    """Scrapes open-access medical journals for case reports and clinical data.

    Usage:
        scraper = MedicalCorpusScraper()
        cases = scraper.scrape_source("japi", max_articles=20)
        scraper.save_scraped_cases(cases, "japi_cases.json")
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else CORPUS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def scrape_source(self, source_key: str, max_articles: int = 50) -> list[dict]:
        """Scrape case reports from a configured source."""
        if source_key not in SOURCES:
            logger.error(f"Unknown source: {source_key}. Available: {list(SOURCES.keys())}")
            return []

        source = SOURCES[source_key]
        logger.info(f"Scraping {source['name']}...")

        try:
            articles = self._get_article_links(source, max_articles)
            cases = []
            for i, url in enumerate(articles):
                logger.info(f"  Processing article {i+1}/{len(articles)}: {url}")
                case = self._extract_case_from_article(url, source)
                if case:
                    case["source"] = source["name"]
                    cases.append(case)
                time.sleep(2)  # Respectful rate limiting

            logger.info(f"Extracted {len(cases)} cases from {source['name']}")
            return cases

        except Exception as e:
            logger.error(f"Error scraping {source_key}: {e}")
            return []

    def _get_article_links(self, source: dict, max_articles: int) -> list[str]:
        """Extract article links from journal archive page."""
        url = f"{source['base_url']}{source['archive_path']}"
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            links = []
            for a_tag in soup.select(source["article_selector"]):
                href = a_tag.get("href", "")
                if href and "case" in href.lower():
                    full_url = href if href.startswith("http") else f"{source['base_url']}{href}"
                    links.append(full_url)
                if len(links) >= max_articles:
                    break

            return links
        except Exception as e:
            logger.error(f"Error fetching article links from {url}: {e}")
            return []

    def _extract_case_from_article(self, url: str, source: dict) -> Optional[dict]:
        """Extract structured case data from an article page."""
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else "Untitled"

            content_div = soup.select_one(source["content_selector"])
            if not content_div:
                content_div = soup.find("article") or soup.find("main")

            if not content_div:
                return None

            full_text = content_div.get_text(separator="\n", strip=True)

            # Try to parse structured sections
            case = {
                "id": f"SCRAPED-{hash(url) % 100000:05d}",
                "title": title_text,
                "url": url,
                "full_text": full_text[:5000],  # Cap at 5000 chars
                "specialty": self._detect_specialty(title_text + " " + full_text[:500]),
                "difficulty": "intermediate",
            }

            # Extract sections if identifiable
            case["presentation"] = self._extract_section(full_text, ["presentation", "case report", "case description", "introduction"])
            case["history"] = self._extract_section(full_text, ["history", "clinical history"])
            case["physical_exam"] = self._extract_section(full_text, ["examination", "physical examination", "clinical examination"])
            case["investigations"] = self._extract_section(full_text, ["investigations", "laboratory", "imaging", "results"])
            case["diagnosis"] = self._extract_section(full_text, ["diagnosis", "final diagnosis", "discussion"])

            return case

        except Exception as e:
            logger.error(f"Error extracting case from {url}: {e}")
            return None

    def _extract_section(self, text: str, keywords: list[str]) -> str:
        """Extract a section of text based on heading keywords."""
        for keyword in keywords:
            pattern = rf"(?i)(?:^|\n)\s*{keyword}\s*[:\n](.+?)(?=\n\s*[A-Z][a-z]+\s*[:\n]|\Z)"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()[:1000]
        return ""

    def _detect_specialty(self, text: str) -> str:
        """Auto-detect specialty from article text."""
        text_lower = text.lower()
        specialty_keywords = {
            "cardiology": ["cardiac", "heart", "coronary", "ecg", "myocardial", "arrhythmia", "valve"],
            "respiratory": ["pulmonary", "lung", "pneumonia", "copd", "asthma", "tuberculosis", "respiratory"],
            "infectious": ["infection", "fever", "malaria", "dengue", "hiv", "sepsis", "antibiotic"],
            "neurology": ["brain", "stroke", "seizure", "neurological", "meningitis", "neuropathy"],
            "gastro": ["liver", "hepat", "gastro", "pancrea", "intestin", "colon", "bowel"],
            "emergency": ["emergency", "trauma", "poisoning", "resuscitation", "shock", "acute"],
        }

        scores = {}
        for specialty, keywords in specialty_keywords.items():
            scores[specialty] = sum(1 for kw in keywords if kw in text_lower)

        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "general"

    def scrape_medmcqa(self, output_file: str = "medmcqa_cases.json") -> list[dict]:
        """Download and process MedMCQA dataset (Indian medical exam questions).

        MedMCQA is available on HuggingFace: https://huggingface.co/datasets/medmcqa
        This method provides the infrastructure to ingest it.
        """
        logger.info("MedMCQA ingestion: Use `datasets` library to load from HuggingFace")
        logger.info("  from datasets import load_dataset")
        logger.info("  ds = load_dataset('openlifescienceai/medmcqa')")

        # Return instructions for manual setup
        return []

    def save_scraped_cases(self, cases: list[dict], filename: str):
        """Save scraped cases to JSON file in corpus directory."""
        output_path = self.output_dir / filename
        with open(output_path, "w") as f:
            json.dump(cases, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(cases)} cases to {output_path}")

    def ingest_pdf(self, pdf_path: str) -> list[dict]:
        """Extract case data from a PDF file (medical textbook or journal)."""
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed. Run: pip install pdfplumber")
            return []

        cases = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

                # Split into potential case boundaries
                case_sections = re.split(r"(?i)\n(?:case\s+\d+|case\s+report|clinical\s+case)", full_text)

                for i, section in enumerate(case_sections[1:], 1):  # Skip first (before any case)
                    if len(section.strip()) < 100:
                        continue
                    case = {
                        "id": f"PDF-{Path(pdf_path).stem}-{i:03d}",
                        "title": f"Case {i} from {Path(pdf_path).name}",
                        "full_text": section.strip()[:5000],
                        "specialty": self._detect_specialty(section[:500]),
                        "difficulty": "intermediate",
                        "source": f"PDF: {Path(pdf_path).name}",
                    }
                    cases.append(case)

            logger.info(f"Extracted {len(cases)} cases from {pdf_path}")
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")

        return cases
