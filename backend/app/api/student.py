from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.session import session

router = APIRouter()


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    year_level: Optional[str] = None


@router.get("/profile")
async def get_profile():
    return session.get_student_profile()


@router.put("/profile")
async def update_profile(update: ProfileUpdate):
    profile = session.get_student_profile()
    if update.name:
        profile["name"] = update.name
    if update.year_level:
        profile["year_level"] = update.year_level
    return profile


@router.get("/biases")
async def get_biases():
    return session.detect_biases()


@router.get("/knowledge-graph")
async def get_knowledge_graph():
    return session.build_knowledge_graph()
