from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.rag.generator import CaseGenerator

router = APIRouter()
case_generator = CaseGenerator()

SPECIALTIES = [
    {"id": "cardiology", "name": "Cardiology", "icon": "heart", "cases_available": 30, "description": "Heart failure, ACS, arrhythmias, valvular disease"},
    {"id": "respiratory", "name": "Respiratory", "icon": "lungs", "cases_available": 25, "description": "Pneumonia, COPD, TB, ILD, asthma"},
    {"id": "infectious", "name": "Infectious Disease", "icon": "virus", "cases_available": 28, "description": "Dengue, malaria, typhoid, scrub typhus, leptospirosis"},
    {"id": "neurology", "name": "Neurology", "icon": "brain", "cases_available": 20, "description": "Stroke, meningitis, seizures, GBS, NCC"},
    {"id": "gastro", "name": "Gastroenterology", "icon": "microscope", "cases_available": 22, "description": "Liver disease, pancreatitis, GI bleeds, celiac"},
    {"id": "emergency", "name": "Emergency Medicine", "icon": "alert", "cases_available": 35, "description": "DKA, sepsis, snake bite, poisoning, anaphylaxis"},
]


class CaseRequest(BaseModel):
    specialty: str
    difficulty: str = "intermediate"
    year_level: str = "final_year"


class CaseActionRequest(BaseModel):
    case_id: str
    action_type: str
    student_input: Optional[str] = None


class DiagnosisRequest(BaseModel):
    case_id: str
    diagnosis: str
    reasoning: str = ""


@router.get("/specialties")
async def get_specialties():
    return {"specialties": SPECIALTIES}


@router.post("/generate")
async def generate_case(request: CaseRequest):
    try:
        case = case_generator.generate_case(
            specialty=request.specialty,
            difficulty=request.difficulty,
            year_level=request.year_level,
        )
        return case
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corpus-stats")
async def get_corpus_stats():
    """Get RAG corpus statistics."""
    return case_generator.get_corpus_stats()


@router.get("/{case_id}")
async def get_case(case_id: str):
    case = case_generator.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/action")
async def case_action(case_id: str, request: CaseActionRequest):
    result = case_generator.process_action(case_id, request.action_type, request.student_input)
    return result


@router.post("/{case_id}/diagnose")
async def submit_diagnosis(case_id: str, request: DiagnosisRequest):
    result = case_generator.evaluate_diagnosis(case_id, request.diagnosis, request.reasoning)
    return result
