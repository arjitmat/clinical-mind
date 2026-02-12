"""Data models for AI Patient Simulation."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class EmotionalState(str, Enum):
    """Patient emotional states."""
    CALM = "calm"
    CONCERNED = "concerned"
    ANXIOUS = "anxious"
    DEFENSIVE = "defensive"


class PatientGender(str, Enum):
    """Patient gender categories for avatar selection."""
    MALE = "male"
    FEMALE = "female"
    PREGNANT = "pregnant"


class RapportLevel(int, Enum):
    """Rapport level between student and patient (1-5 scale)."""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    GOOD = 4
    EXCELLENT = 5


class FeedbackType(str, Enum):
    """Types of AI tutor feedback."""
    POSITIVE = "positive"  # ✓ green
    WARNING = "warning"    # ⚠️ amber
    CRITICAL = "critical"  # ✗ red


class PatientProfile(BaseModel):
    """Patient demographic and clinical profile."""
    age: int
    gender: PatientGender
    name: str
    chief_complaint: str
    setting: str  # "ER", "OPD", "ward", etc.
    specialty: str
    difficulty: str  # "beginner", "intermediate", "advanced"

    # Hidden diagnosis (not shown to student)
    actual_diagnosis: str
    key_history_points: List[str]
    physical_exam_findings: dict

    # Initial state
    initial_emotional_state: EmotionalState = EmotionalState.CONCERNED


class SimulationMessage(BaseModel):
    """A message in the patient-student conversation."""
    role: str  # "student" or "patient"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    emotional_state: Optional[EmotionalState] = None  # Only for patient messages


class TutorFeedback(BaseModel):
    """Real-time feedback from AI tutor."""
    type: FeedbackType
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class EvaluationMetrics(BaseModel):
    """Evaluation metrics for student communication."""
    empathy_score: int  # 1-5
    communication_quality: int  # 1-5
    clinical_reasoning: int  # 1-5
    open_ended_questions: int  # count
    acknowledged_distress: bool
    bedside_manner: int  # 1-5


class SimulationState(BaseModel):
    """Complete state of an active simulation."""
    case_id: str
    patient_profile: PatientProfile

    # Current state
    emotional_state: EmotionalState
    rapport_level: RapportLevel

    # Conversation history
    messages: List[SimulationMessage] = []
    tutor_feedback: List[TutorFeedback] = []

    # Evaluation
    evaluation: Optional[EvaluationMetrics] = None

    # Metadata
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    student_diagnosis: Optional[str] = None
    student_reasoning: Optional[str] = None


# === API Request/Response Models ===

class StartSimulationRequest(BaseModel):
    """Request to start a new simulation."""
    specialty: str = "general_medicine"
    difficulty: str = "intermediate"
    year_level: str = "final_year"  # for future use


class StartSimulationResponse(BaseModel):
    """Response when starting a simulation."""
    case_id: str
    patient_info: dict  # Safe patient info (no diagnosis)
    avatar_path: str  # e.g., "/avatars/male/concerned.svg"
    setting_context: str
    initial_message: str  # Patient's first words


class SendMessageRequest(BaseModel):
    """Student sending a message to the patient."""
    case_id: str
    student_message: str


class SendMessageResponse(BaseModel):
    """Patient response + state updates + tutor feedback."""
    patient_response: str
    emotional_state: EmotionalState
    rapport_level: RapportLevel
    tutor_feedback: List[TutorFeedback]
    avatar_path: str  # May change based on emotional state


class CompleteSimulationRequest(BaseModel):
    """Student completing the simulation with diagnosis."""
    case_id: str
    diagnosis: str
    reasoning: str


class CognitiveAutopsy(BaseModel):
    """Deep analysis of student's diagnostic process."""
    mental_model: str
    breaking_point: str  # When/where reasoning broke down
    what_you_missed: List[str]
    why_you_missed_it: str
    pattern_across_cases: Optional[str] = None
    prediction: str  # What they'll likely miss in future


class CompleteSimulationResponse(BaseModel):
    """Response after simulation completion."""
    correct_diagnosis: str
    diagnosis_correct: bool
    cognitive_autopsy: CognitiveAutopsy
    evaluation: EvaluationMetrics
