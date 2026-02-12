from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# In-memory student data (demo purposes)
DEMO_STUDENT = {
    "id": "student-001",
    "name": "Medical Student",
    "year_level": "final_year",
    "cases_completed": 48,
    "accuracy": 75,
    "avg_time": 10,
    "percentile": 15,
    "specialty_scores": {
        "cardiology": 82,
        "respiratory": 65,
        "infectious": 78,
        "neurology": 45,
        "gastro": 70,
        "emergency": 55,
    },
    "weak_areas": ["neurology", "emergency"],
}


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    year_level: Optional[str] = None


@router.get("/profile")
async def get_profile():
    return DEMO_STUDENT


@router.put("/profile")
async def update_profile(update: ProfileUpdate):
    if update.name:
        DEMO_STUDENT["name"] = update.name
    if update.year_level:
        DEMO_STUDENT["year_level"] = update.year_level
    return DEMO_STUDENT


@router.get("/biases")
async def get_biases():
    from app.core.analytics.bias_detector import BiasDetector
    detector = BiasDetector()
    return detector.generate_demo_report()


@router.get("/knowledge-graph")
async def get_knowledge_graph():
    from app.core.analytics.knowledge_graph import KnowledgeGraphBuilder
    builder = KnowledgeGraphBuilder()
    return builder.build_demo_graph()
