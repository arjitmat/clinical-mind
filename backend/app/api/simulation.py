"""API endpoints for AI Patient Simulation."""
import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.core.agents.orchestrator import SimulationOrchestrator
from app.models.simulation import (
    StartSimulationRequest,
    StartSimulationResponse,
    SendMessageRequest,
    SendMessageResponse,
    CompleteSimulationRequest,
    CompleteSimulationResponse,
    CognitiveAutopsy,
    EvaluationMetrics,
    FeedbackType,
    TutorFeedback,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize orchestrator (singleton)
orchestrator = SimulationOrchestrator()


@router.post("/start", response_model=StartSimulationResponse)
async def start_simulation(request: StartSimulationRequest):
    """
    Start a new patient simulation.

    Returns:
        - case_id: Unique identifier for this simulation
        - patient_info: Safe patient demographics (no diagnosis)
        - avatar_path: Path to avatar SVG
        - setting_context: Where the encounter takes place
        - initial_message: Patient's first words
    """
    try:
        simulation = orchestrator.start_simulation(
            specialty=request.specialty,
            difficulty=request.difficulty,
        )

        # Build avatar path based on gender and emotional state
        avatar_path = (
            f"/avatars/{simulation.patient_profile.gender.value}/"
            f"{simulation.emotional_state.value}.svg"
        )

        # Safe patient info (no diagnosis)
        patient_info = {
            "age": simulation.patient_profile.age,
            "gender": simulation.patient_profile.gender.value,
            "name": simulation.patient_profile.name,
            "chief_complaint": simulation.patient_profile.chief_complaint,
        }

        # Get initial patient message
        initial_message = simulation.messages[0].content

        return StartSimulationResponse(
            case_id=simulation.case_id,
            patient_info=patient_info,
            avatar_path=avatar_path,
            setting_context=simulation.patient_profile.setting,
            initial_message=initial_message,
        )

    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """
    Student sends a message to the patient.

    Multi-agent pipeline:
    1. Evaluator analyzes student message
    2. Updates emotional state & rapport based on communication quality
    3. Patient responds based on new emotional state
    4. Tutor provides real-time Socratic feedback

    Returns:
        - patient_response: What patient says
        - emotional_state: Current patient emotion
        - rapport_level: Current rapport (1-5)
        - tutor_feedback: Real-time feedback from AI tutor
        - avatar_path: Updated avatar (may change with emotion)
    """
    try:
        # Process message through multi-agent pipeline
        simulation = orchestrator.process_student_message(
            case_id=request.case_id,
            student_message=request.student_message,
        )

        # Get latest patient message
        patient_messages = [msg for msg in simulation.messages if msg.role == "patient"]
        latest_patient_message = patient_messages[-1].content

        # Get feedback from this interaction (last few feedback items)
        recent_feedback = simulation.tutor_feedback[-2:]  # Evaluator + Tutor feedback

        # Update avatar path based on new emotional state
        avatar_path = (
            f"/avatars/{simulation.patient_profile.gender.value}/"
            f"{simulation.emotional_state.value}.svg"
        )

        return SendMessageResponse(
            patient_response=latest_patient_message,
            emotional_state=simulation.emotional_state,
            rapport_level=simulation.rapport_level,
            tutor_feedback=recent_feedback,
            avatar_path=avatar_path,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete", response_model=CompleteSimulationResponse)
async def complete_simulation(request: CompleteSimulationRequest):
    """
    Complete simulation and get cognitive autopsy.

    Student provides their diagnosis and reasoning.
    System performs deep analysis of their diagnostic process.

    Returns:
        - correct_diagnosis: What it actually was
        - diagnosis_correct: Boolean
        - cognitive_autopsy: Deep analysis of thinking process
        - evaluation: Overall communication metrics
    """
    try:
        # Mark simulation as complete
        simulation = orchestrator.complete_simulation(
            case_id=request.case_id,
            diagnosis=request.diagnosis,
            reasoning=request.reasoning,
        )

        # Check if diagnosis is correct
        correct_diagnosis = simulation.patient_profile.actual_diagnosis
        diagnosis_correct = (
            request.diagnosis.lower().strip() in correct_diagnosis.lower()
        )

        # Generate cognitive autopsy
        # TODO: Call Opus API for deep analysis
        # For now, provide a structured template
        cognitive_autopsy = CognitiveAutopsy(
            mental_model=(
                f"You approached this case with a '{request.diagnosis}' framework. "
                "Your initial hypothesis shaped how you interpreted the symptoms."
            ),
            breaking_point=(
                "Your reasoning process needed more systematic differential diagnosis. "
                "Consider using a structured approach to avoid premature closure."
            ),
            what_you_missed=simulation.patient_profile.key_history_points[:2],
            why_you_missed_it=(
                "These details may have been missed due to closed-ended questioning "
                "or not building enough rapport for the patient to share freely."
            ),
            prediction=(
                "In future cases with similar presentations, remember to: "
                "1) Build rapport first, 2) Use open-ended questions, "
                "3) Consider multiple differentials before anchoring."
            ),
        )

        # Calculate evaluation metrics based on simulation history
        evaluation = _calculate_evaluation_metrics(simulation)

        return CompleteSimulationResponse(
            correct_diagnosis=correct_diagnosis,
            diagnosis_correct=diagnosis_correct,
            cognitive_autopsy=cognitive_autopsy,
            evaluation=evaluation,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{case_id}")
async def get_simulation_status(case_id: str):
    """Get current simulation state (for debugging)."""
    try:
        simulation = orchestrator.get_simulation(case_id)
        return {
            "case_id": simulation.case_id,
            "emotional_state": simulation.emotional_state.value,
            "rapport_level": simulation.rapport_level.value,
            "message_count": len(simulation.messages),
            "completed": simulation.completed_at is not None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _calculate_evaluation_metrics(simulation) -> EvaluationMetrics:
    """Calculate overall evaluation metrics from simulation history."""

    # Count open-ended questions
    student_messages = [msg.content for msg in simulation.messages if msg.role == "student"]
    open_ended_markers = ["tell me", "describe", "how do you", "what happened", "when did"]

    open_ended_count = sum(
        1
        for msg in student_messages
        if any(marker in msg.lower() for marker in open_ended_markers)
    )

    # Check if distress was acknowledged
    empathy_markers = ["understand", "worried", "difficult", "sorry", "must be"]
    acknowledged_distress = any(
        any(marker in msg.lower() for marker in empathy_markers)
        for msg in student_messages
    )

    # Calculate scores based on feedback history
    positive_feedback_count = sum(
        1 for fb in simulation.tutor_feedback if fb.type == FeedbackType.POSITIVE
    )
    critical_feedback_count = sum(
        1 for fb in simulation.tutor_feedback if fb.type == FeedbackType.CRITICAL
    )

    total_feedback = len(simulation.tutor_feedback)
    feedback_ratio = (
        positive_feedback_count / total_feedback if total_feedback > 0 else 0.5
    )

    # Score calculations (1-5 scale)
    empathy_score = min(5, max(1, int(feedback_ratio * 5)))
    communication_quality = min(5, max(1, int(simulation.rapport_level.value)))
    bedside_manner = min(5, max(1, int(simulation.rapport_level.value)))
    clinical_reasoning = 3  # Default, would be calculated from diagnosis accuracy

    return EvaluationMetrics(
        empathy_score=empathy_score,
        communication_quality=communication_quality,
        clinical_reasoning=clinical_reasoning,
        open_ended_questions=open_ended_count,
        acknowledged_distress=acknowledged_distress,
        bedside_manner=bedside_manner,
    )
