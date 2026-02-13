"""API routes for the multi-agent hospital ecosystem."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.agents.orchestrator import orchestrator
from app.core.rag.generator import CaseGenerator

router = APIRouter()
case_generator = CaseGenerator()


class InitializeRequest(BaseModel):
    case_id: str


class AgentActionRequest(BaseModel):
    session_id: str
    action_type: str
    student_input: Optional[str] = None


@router.post("/initialize")
async def initialize_agents(request: InitializeRequest):
    """Initialize multi-agent session for a case.

    Returns initial messages from patient, nurse, and senior doctor.
    """
    case = case_generator.get_case(request.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    result = orchestrator.initialize_session(case)
    return result


@router.post("/action")
async def agent_action(request: AgentActionRequest):
    """Process a student action through the multi-agent system.

    action_type options:
    - talk_to_patient: Talk to the patient
    - ask_nurse: Ask the nurse
    - consult_senior: Consult the senior doctor
    - examine_patient: Perform examination
    - order_investigation: Order tests
    """
    result = orchestrator.process_action(
        session_id=request.session_id,
        action_type=request.action_type,
        student_input=request.student_input,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/vitals/{session_id}")
async def get_vitals(session_id: str):
    """Get current vital signs and urgency status for a session."""
    vitals = orchestrator.get_session_vitals(session_id)
    if not vitals:
        raise HTTPException(status_code=404, detail="Session not found")
    return vitals
