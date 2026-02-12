"""
Profile-based case selection endpoint
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import random
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class StudentProfile(BaseModel):
    yearLevel: str  # final_year, internship, residency, practicing
    comfortableSpecialties: List[str]
    setting: str  # urban, rural, community


class CaseSelectionRequest(BaseModel):
    profile: StudentProfile
    feature: str  # simulation, reasoning-chain, adversarial, bias-interruption


class CaseSelectionResponse(BaseModel):
    specialty: str
    difficulty: str
    setting: str
    why_selected: str


@router.post("/select-case", response_model=CaseSelectionResponse)
async def select_case_for_profile(request: CaseSelectionRequest):
    """
    Select appropriate case based on student profile.

    Logic:
    1. Map year level to difficulty
    2. Select specialty (70% comfortable, 30% challenge)
    3. Match setting preference
    4. Return case parameters for simulation to use
    """

    profile = request.profile
    feature = request.feature

    # 1. Determine difficulty based on year level
    difficulty_map = {
        "final_year": ["beginner", "intermediate"],
        "internship": ["intermediate"],
        "residency": ["intermediate", "advanced"],
        "practicing": ["advanced"],
    }

    difficulties = difficulty_map.get(profile.yearLevel, ["intermediate"])
    difficulty = random.choice(difficulties)

    # 2. Select specialty
    all_specialties = [
        "cardiology", "respiratory", "infectious", "neurology",
        "gastro", "emergency", "pediatrics", "obstetrics"
    ]

    if profile.comfortableSpecialties and len(profile.comfortableSpecialties) > 0:
        # 70% from comfortable areas, 30% challenge
        if random.random() < 0.7:
            specialty = random.choice(profile.comfortableSpecialties)
            reason_specialty = f"your comfort area ({specialty})"
        else:
            # Challenge: pick from non-comfortable
            challenge_specialties = [
                s for s in all_specialties
                if s not in profile.comfortableSpecialties
            ]
            if challenge_specialties:
                specialty = random.choice(challenge_specialties)
                reason_specialty = f"a challenge area ({specialty})"
            else:
                specialty = random.choice(all_specialties)
                reason_specialty = specialty
    else:
        specialty = random.choice(all_specialties)
        reason_specialty = specialty

    # 3. Setting
    setting = profile.setting

    # 4. Feature-specific adjustments
    if feature == "adversarial":
        # Always use challenge specialty for adversarial
        challenge_specialties = [
            s for s in all_specialties
            if s not in (profile.comfortableSpecialties or [])
        ]
        if challenge_specialties:
            specialty = random.choice(challenge_specialties)
            reason_specialty = f"designed to challenge you ({specialty})"

    # Build explanation
    why_selected = f"Selected {difficulty} difficulty case in {reason_specialty}, matching your {setting} setting preference."

    logger.info(
        f"Case selection: {specialty}/{difficulty}/{setting} for {profile.yearLevel} student (feature: {feature})"
    )

    return CaseSelectionResponse(
        specialty=specialty,
        difficulty=difficulty,
        setting=setting,
        why_selected=why_selected,
    )
