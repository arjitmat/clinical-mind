import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env from backend/ directory (local dev); HF Spaces injects env vars directly
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from app.api import cases, student, analytics, agents, simulation, reasoning, adversarial, bias_detection, profile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG system on startup."""
    logger.info("Initializing Clinical-Mind RAG system...")
    from app.core.rag.vector_store import MedicalVectorStore

    store = MedicalVectorStore()
    if store.count() == 0:
        logger.info("Vector store empty — ingesting seed corpus...")
        count = store.ingest_corpus()
        logger.info(f"Ingested {count} document chunks into ChromaDB")
    else:
        logger.info(f"ChromaDB loaded with {store.count()} documents")

    yield

    logger.info("Clinical-Mind shutting down")


app = FastAPI(
    title="Clinical-Mind API",
    description="AI-powered clinical reasoning simulator for medical students",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:7860",
        "https://arjitmat-clinical-mind.hf.space",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router, prefix="/api/cases", tags=["cases"])
app.include_router(student.router, prefix="/api/student", tags=["student"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(reasoning.router, prefix="/api/reasoning", tags=["reasoning"])
app.include_router(adversarial.router, prefix="/api/adversarial", tags=["adversarial"])
app.include_router(bias_detection.router, prefix="/api/bias", tags=["bias-detection"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])


@app.get("/")
async def root():
    return {"message": "Clinical-Mind API", "version": "2.0.0", "rag": "enabled"}


@app.get("/health")
async def health():
    from app.core.rag.vector_store import MedicalVectorStore

    store = MedicalVectorStore()
    return {
        "status": "healthy",
        "rag_documents": store.count(),
        "rag_status": "loaded" if store.count() > 0 else "empty",
    }
