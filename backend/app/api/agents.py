"""API routes for the multi-agent hospital simulation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.agents.orchestrator import orchestrator
from app.core.rag.shared import case_generator

router = APIRouter()


# --- Request Models ---

class InitializeRequest(BaseModel):
    case_id: str
    student_level: str = "intern"
    hospital_setting: str = "medical_college"


class AgentActionRequest(BaseModel):
    session_id: str
    action_type: str
    student_input: Optional[str] = None


class TreatmentRequest(BaseModel):
    session_id: str
    treatment: str


class AdvanceTimeRequest(BaseModel):
    session_id: str
    minutes: int = 30


# --- Endpoints ---

@router.post("/initialize")
async def initialize_agents(request: InitializeRequest):
    """Initialize multi-agent simulation session for a case.

    Accepts student_level to calibrate teaching intensity:
    - mbbs_2nd: Pre-clinical, more guidance
    - mbbs_3rd: Clinical posting, standard
    - intern: Hands-on, less hand-holding
    - pg_aspirant: NEET-PG focus, exam patterns
    - pg_resident: Advanced, minimal guidance

    Returns initial messages from patient, nurse, and senior doctor,
    plus simulation state (vitals, timeline, investigations).
    """
    case = case_generator.get_case(request.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    result = orchestrator.initialize_session(
        case_data=case,
        student_level=request.student_level,
        hospital_setting=request.hospital_setting,
    )
    return result


@router.post("/action")
async def agent_action(request: AgentActionRequest):
    """Process a student action through the simulation pipeline.

    action_type options:
    - talk_to_patient: Talk to the patient (family may interject)
    - ask_nurse: Ask Nurse Priya
    - consult_senior: Consult Dr. Sharma (Socratic teaching)
    - talk_to_family: Talk to patient's family member (cultural context, Hinglish)
    - ask_lab: Talk to Lab Tech Ramesh (investigation status, sample info)
    - examine_patient: Perform physical examination (triggers exam modal)
    - order_investigation: Order tests (Lab Tech processes, realistic delays)
    - order_treatment: Order treatment (safety validated, effects modeled)
    - team_huddle: All 5 agents discuss the case together

    Each action advances the simulation clock and checks the complication engine.
    Returns agent responses, updated vitals, timeline events, investigation status,
    and any triggered complications.
    """
    result = orchestrator.process_action(
        session_id=request.session_id,
        action_type=request.action_type,
        student_input=request.student_input,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/advance-time")
async def advance_time(request: AdvanceTimeRequest):
    """Advance simulation time (e.g., waiting for investigation results).

    Evolves vitals, checks for ready investigations, triggers events.
    """
    result = orchestrator.advance_time(
        session_id=request.session_id,
        minutes=request.minutes,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/vitals/{session_id}")
async def get_vitals(session_id: str):
    """Get current vital signs with trends and trajectory."""
    vitals = orchestrator.get_session_vitals(session_id)
    if not vitals:
        raise HTTPException(status_code=404, detail="Session not found")
    return vitals


@router.get("/investigations/{session_id}")
async def get_investigations(session_id: str):
    """Get status of all ordered investigations."""
    investigations = orchestrator.get_investigation_status(session_id)
    if investigations is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"investigations": investigations}


@router.get("/timeline/{session_id}")
async def get_timeline(session_id: str):
    """Get complete simulation timeline."""
    timeline = orchestrator.get_timeline(session_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"timeline": timeline}
