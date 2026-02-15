from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.rag.shared import case_generator
from app.core.session import session

router = APIRouter()

SPECIALTIES = [
    {"id": "cardiology", "name": "Cardiology", "icon": "heart", "cases_available": 12, "description": "STEMI, heart failure, IE, AF, aortic dissection, rheumatic heart disease"},
    {"id": "respiratory", "name": "Respiratory", "icon": "lungs", "cases_available": 10, "description": "Pneumonia, COPD, TB pleural effusion, asthma, ILD, lung cancer"},
    {"id": "infectious", "name": "Infectious Disease", "icon": "virus", "cases_available": 10, "description": "Dengue, malaria, typhoid, scrub typhus, leptospirosis, HIV"},
    {"id": "neurology", "name": "Neurology", "icon": "brain", "cases_available": 10, "description": "Stroke, meningitis, GBS, myasthenia gravis, epilepsy, Parkinson's"},
    {"id": "gastro", "name": "Gastroenterology", "icon": "microscope", "cases_available": 10, "description": "Liver abscess, cirrhosis, pancreatitis, IBD, GI bleed, celiac, HCC"},
    {"id": "emergency", "name": "Emergency Medicine", "icon": "alert", "cases_available": 10, "description": "DKA, snake bite, poisoning, burns, anaphylaxis, acute MI"},
    {"id": "nephrology", "name": "Nephrology", "icon": "droplet", "cases_available": 10, "description": "CKD, nephrotic syndrome, AKI, RPGN, RTA, lupus nephritis"},
    {"id": "endocrinology", "name": "Endocrinology", "icon": "activity", "cases_available": 10, "description": "Thyroid storm, Addison crisis, Cushing, pheochromocytoma, HHS"},
    {"id": "pediatrics", "name": "Pediatrics", "icon": "baby", "cases_available": 10, "description": "Bronchiolitis, TOF, Kawasaki, malnutrition, thalassemia, ALL"},
    {"id": "obstetrics", "name": "Obstetrics & Gynecology", "icon": "heart-pulse", "cases_available": 10, "description": "Eclampsia, ectopic, PPH, PCOS, placenta previa, cervical cancer"},
    {"id": "hematology", "name": "Hematology", "icon": "test-tubes", "cases_available": 10, "description": "IDA, sickle cell, ITP, DIC, CML, hemophilia, TTP"},
    {"id": "psychiatry", "name": "Psychiatry", "icon": "brain-cog", "cases_available": 10, "description": "Schizophrenia, depression, bipolar, delirium tremens, OCD, NMS"},
    {"id": "dermatology", "name": "Dermatology", "icon": "scan", "cases_available": 10, "description": "SJS/TEN, leprosy, pemphigus, psoriasis, DRESS, vitiligo"},
    {"id": "orthopedics", "name": "Orthopedics", "icon": "bone", "cases_available": 10, "description": "Fractures, septic arthritis, osteosarcoma, Pott spine, AVN, ACL"},
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

    # Record result in session tracker for dynamic analytics
    case = case_generator.get_case(case_id)
    if case and "error" not in result:
        session.record_case_result(
            case_id=case_id,
            specialty=case.get("specialty", ""),
            difficulty=case.get("difficulty", ""),
            diagnosis=request.diagnosis,
            correct_diagnosis=result.get("correct_diagnosis", case.get("diagnosis", "")),
            is_correct=result.get("is_correct", False),
            accuracy_score=result.get("accuracy_score", 0),
        )

    return result
