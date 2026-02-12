"""Multi-Agent Orchestrator - Coordinates Patient, Evaluator, and Tutor agents."""
import logging
import uuid
from datetime import datetime
from typing import Dict, List

from app.core.agents.patient import PatientAgent
from app.core.agents.evaluator import EvaluatorAgent
from app.core.agents.tutor import SocraticTutor
from app.models.simulation import (
    SimulationState,
    PatientProfile,
    EmotionalState,
    RapportLevel,
    SimulationMessage,
    TutorFeedback,
    PatientGender,
)

logger = logging.getLogger(__name__)


class SimulationOrchestrator:
    """
    Orchestrates multi-agent simulation.

    Flow:
    1. Student sends message
    2. Evaluator analyzes message → updates emotional_state & rapport → provides feedback
    3. Patient generates response based on new emotional state
    4. Tutor provides additional guidance (Socratic method)
    5. All updates returned to student
    """

    def __init__(self):
        self.patient_agent = PatientAgent()
        self.evaluator_agent = EvaluatorAgent()
        self.tutor_agent = SocraticTutor()

        # In-memory storage for active simulations
        # TODO: Replace with database in production
        self.active_simulations: Dict[str, SimulationState] = {}

    def start_simulation(
        self,
        specialty: str = "general_medicine",
        difficulty: str = "intermediate",
    ) -> SimulationState:
        """Initialize a new patient simulation."""

        # Generate case using existing RAG system
        # For now, use a sample case
        patient_profile, initial_greeting = self._generate_patient_profile(specialty, difficulty)

        case_id = str(uuid.uuid4())

        # Create simulation state
        simulation = SimulationState(
            case_id=case_id,
            patient_profile=patient_profile,
            emotional_state=patient_profile.initial_emotional_state,
            rapport_level=RapportLevel.MODERATE,  # Start neutral
            messages=[
                SimulationMessage(
                    role="patient",
                    content=initial_greeting,
                    emotional_state=patient_profile.initial_emotional_state,
                )
            ],
        )

        # Store in memory
        self.active_simulations[case_id] = simulation

        logger.info(f"Started simulation {case_id}: {specialty} / {difficulty}")
        return simulation

    def process_student_message(
        self,
        case_id: str,
        student_message: str,
    ) -> SimulationState:
        """
        Process student message through multi-agent pipeline.

        Returns updated simulation state with:
        - Patient response
        - Updated emotional state & rapport
        - Tutor feedback
        """

        if case_id not in self.active_simulations:
            raise ValueError(f"Simulation {case_id} not found")

        simulation = self.active_simulations[case_id]

        # Add student message to history
        simulation.messages.append(
            SimulationMessage(role="student", content=student_message)
        )

        # STEP 1: Evaluator analyzes student message
        new_emotional_state, new_rapport, evaluator_feedback = (
            self.evaluator_agent.evaluate_message(
                student_message=student_message,
                current_emotional_state=simulation.emotional_state,
                current_rapport=simulation.rapport_level,
            )
        )

        # Update simulation state
        simulation.emotional_state = new_emotional_state
        simulation.rapport_level = new_rapport
        simulation.tutor_feedback.append(evaluator_feedback)

        logger.info(
            f"Sim {case_id}: Emotional {new_emotional_state.value}, "
            f"Rapport {new_rapport.value}"
        )

        # STEP 2: Patient generates response based on new emotional state
        conversation_history = [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in simulation.messages
        ]

        patient_response = self.patient_agent.generate_response(
            student_message=student_message,
            patient_profile=simulation.patient_profile.model_dump(),
            emotional_state=new_emotional_state,
            conversation_history=conversation_history[:-1],  # Exclude student's latest message
        )

        # Add patient response to history
        simulation.messages.append(
            SimulationMessage(
                role="patient",
                content=patient_response,
                emotional_state=new_emotional_state,
            )
        )

        # STEP 3: Tutor provides Socratic feedback
        case_context = {
            "chief_complaint": simulation.patient_profile.chief_complaint,
            "specialty": simulation.patient_profile.specialty,
            "difficulty": simulation.patient_profile.difficulty,
        }

        tutor_response = self.tutor_agent.respond(
            student_message=student_message,
            case_context=case_context,
        )

        # Add tutor feedback
        simulation.tutor_feedback.append(
            TutorFeedback(
                type="warning",  # Tutor is always guidance, not positive/negative
                message=tutor_response,
            )
        )

        return simulation

    def complete_simulation(
        self,
        case_id: str,
        diagnosis: str,
        reasoning: str,
    ) -> SimulationState:
        """Mark simulation as complete and prepare for cognitive autopsy."""

        if case_id not in self.active_simulations:
            raise ValueError(f"Simulation {case_id} not found")

        simulation = self.active_simulations[case_id]
        simulation.completed_at = datetime.now()
        simulation.student_diagnosis = diagnosis
        simulation.student_reasoning = reasoning

        logger.info(f"Completed simulation {case_id}: {diagnosis}")
        return simulation

    def get_simulation(self, case_id: str) -> SimulationState:
        """Retrieve simulation state."""
        if case_id not in self.active_simulations:
            raise ValueError(f"Simulation {case_id} not found")
        return self.active_simulations[case_id]

    def _generate_patient_profile(
        self,
        specialty: str,
        difficulty: str,
    ) -> tuple[PatientProfile, str]:
        """Generate patient profile - integrates with RAG system. Returns (profile, initial_message)."""

        # TODO: Use RAG system to generate from medical case corpus
        # For now, return a sample case

        if specialty == "cardiology" or specialty == "general_medicine":
            profile = PatientProfile(
                age=42,
                gender=PatientGender.MALE,
                name="Rajesh Kumar",
                chief_complaint="chest pain for 2 hours",
                setting="Emergency Room",
                specialty="cardiology",
                difficulty=difficulty,
                actual_diagnosis="Cocaine-induced acute coronary syndrome",
                key_history_points=[
                    "Chest pain started suddenly 2 hours ago",
                    "Pain is in the center of chest, radiating to left arm",
                    "Associated with sweating and nausea",
                    "History of cocaine use (used last night)",
                    "Smoker for 10 years",
                    "No previous cardiac history",
                ],
                physical_exam_findings={
                    "vitals": "BP 160/95, HR 110, RR 22, SpO2 96%",
                    "general": "Diaphoretic, anxious",
                    "cardiac": "S1 S2 normal, no murmurs",
                    "lungs": "Clear bilaterally",
                },
                initial_emotional_state=EmotionalState.ANXIOUS,
            )
            initial_message = "*breathing heavily, hand on chest*\n\nDoc, my chest has been hurting really bad for the past couple hours and it's freaking me out... I think something's wrong with my heart!"
            return profile, initial_message

        elif specialty == "obstetrics" or "pregnancy" in specialty.lower():
            profile = PatientProfile(
                age=28,
                gender=PatientGender.PREGNANT,
                name="Priya Sharma",
                chief_complaint="severe headache and blurred vision",
                setting="Obstetric Emergency",
                specialty="obstetrics",
                difficulty=difficulty,
                actual_diagnosis="Preeclampsia with severe features",
                key_history_points=[
                    "28 weeks pregnant (first pregnancy)",
                    "Severe headache for past 6 hours",
                    "Vision has become blurry",
                    "Swelling in face and hands since yesterday",
                    "No previous high blood pressure",
                    "Epigastric pain started 1 hour ago",
                ],
                physical_exam_findings={
                    "vitals": "BP 165/105, HR 95, RR 18",
                    "general": "Facial edema, anxious",
                    "neuro": "Reflexes brisk",
                    "obstetric": "Fundal height appropriate, FHR 145",
                },
                initial_emotional_state=EmotionalState.ANXIOUS,
            )
            initial_message = "*holding her head, looking worried*\n\nDoctor, my head is killing me... it's been getting worse all day. And my vision is all blurry. I'm really scared something's wrong with the baby..."
            return profile, initial_message

        else:
            # Default case
            profile = PatientProfile(
                age=35,
                gender=PatientGender.FEMALE,
                name="Anita Desai",
                chief_complaint="fever and cough for 5 days",
                setting="Outpatient Clinic",
                specialty="internal_medicine",
                difficulty=difficulty,
                actual_diagnosis="Community-acquired pneumonia",
                key_history_points=[
                    "Fever up to 102°F for 5 days",
                    "Productive cough with yellowish sputum",
                    "Shortness of breath on exertion",
                    "Right-sided chest pain when coughing",
                    "No recent travel",
                    "No sick contacts",
                ],
                physical_exam_findings={
                    "vitals": "Temp 101.2°F, BP 120/75, HR 92, RR 24, SpO2 93%",
                    "general": "Mild respiratory distress",
                    "lungs": "Decreased breath sounds right lower lobe, crackles",
                    "cardiac": "Normal",
                },
                initial_emotional_state=EmotionalState.CONCERNED,
            )
            initial_message = "*coughing into tissue*\n\nGood morning, doctor. I've had this fever and cough for almost a week now... it's not getting better. I'm a bit worried because I'm starting to feel breathless when I walk around."
            return profile, initial_message
