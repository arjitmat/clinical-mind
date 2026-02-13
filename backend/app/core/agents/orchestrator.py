"""Agent orchestrator — coordinates patient, nurse, and senior doctor agents."""

import logging
import uuid
from typing import Optional

from app.core.agents.patient_agent import PatientAgent
from app.core.agents.nurse_agent import NurseAgent
from app.core.agents.senior_agent import SeniorDoctorAgent

logger = logging.getLogger(__name__)


class AgentSession:
    """Holds the agent instances and state for a single case session."""

    def __init__(self, session_id: str, case_data: dict):
        self.session_id = session_id
        self.case_data = case_data

        # Initialize agents
        self.patient = PatientAgent()
        self.nurse = NurseAgent()
        self.senior = SeniorDoctorAgent()

        # Configure with case data
        self.patient.configure(case_data)
        self.nurse.configure(case_data)
        self.senior.configure(case_data)

        # Track conversation state
        self.message_history: list[dict] = []
        self.stages_revealed: set[int] = set()
        self.diagnosis_submitted = False

    def get_vitals(self) -> dict:
        """Return current vital signs with nurse's urgency assessment."""
        vitals = self.case_data.get("vital_signs", {})
        return {
            "vitals": vitals,
            "urgency_level": self.nurse.urgency_level,
            "patient_distress": self.patient.distress_level,
        }


class AgentOrchestrator:
    """Coordinates all hospital agents for multi-agent case interactions."""

    def __init__(self):
        self.sessions: dict[str, AgentSession] = {}

    def initialize_session(self, case_data: dict) -> dict:
        """Create a new agent session for a case.

        Returns initial messages from all agents (patient greeting, nurse report,
        senior guidance).
        """
        session_id = str(uuid.uuid4())[:8]
        session = AgentSession(session_id, case_data)
        self.sessions[session_id] = session

        # Gather initial messages from all agents
        initial_messages = []

        # 1. Nurse gives initial report
        nurse_report = session.nurse.get_initial_report()
        initial_messages.append(nurse_report)

        # 2. Patient greets
        patient_greeting = session.patient.get_initial_greeting()
        initial_messages.append(patient_greeting)

        # 3. Senior doctor gives initial guidance
        senior_guidance = session.senior.get_initial_guidance()
        initial_messages.append(senior_guidance)

        # Store in history
        session.message_history.extend(initial_messages)

        return {
            "session_id": session_id,
            "messages": initial_messages,
            "vitals": session.get_vitals(),
        }

    def process_action(
        self,
        session_id: str,
        action_type: str,
        student_input: Optional[str] = None,
    ) -> dict:
        """Process a student action and get multi-agent responses.

        action_type can be:
        - 'talk_to_patient': Student talks to the patient
        - 'ask_nurse': Student asks the nurse something
        - 'consult_senior': Student discusses with senior doctor
        - 'examine_patient': Student performs examination (triggers nurse + patient)
        - 'order_investigation': Student orders tests (triggers nurse response)
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found", "messages": []}

        case_context = {
            "chief_complaint": session.case_data.get("chief_complaint", ""),
            "specialty": session.case_data.get("specialty", ""),
            "difficulty": session.case_data.get("difficulty", ""),
        }

        messages = []

        if action_type == "talk_to_patient":
            # Student talks to patient, patient responds
            patient_response = session.patient.respond(
                student_input or "Tell me about your problem",
                case_context,
            )
            messages.append(patient_response)

        elif action_type == "ask_nurse":
            # Student asks nurse
            nurse_response = session.nurse.respond(
                student_input or "What are the current vitals?",
                case_context,
            )
            messages.append(nurse_response)

        elif action_type == "consult_senior":
            # Student discusses with senior doctor
            senior_response = session.senior.respond(
                student_input or "What do you think about this case?",
                case_context,
            )
            messages.append(senior_response)

        elif action_type == "examine_patient":
            # Physical examination — patient reacts, nurse assists
            patient_response = session.patient.respond(
                "The doctor is examining you now. How do you feel?",
                case_context,
            )
            messages.append(patient_response)

            nurse_response = session.nurse.respond(
                f"Student is performing physical examination. Key findings to report: {student_input or 'general exam'}",
                case_context,
            )
            messages.append(nurse_response)

        elif action_type == "order_investigation":
            # Order tests — nurse acknowledges and reports
            nurse_response = session.nurse.respond(
                f"Student has ordered: {student_input or 'routine investigations'}. Report the findings.",
                case_context,
            )
            messages.append(nurse_response)

        else:
            # Default: route to senior doctor
            senior_response = session.senior.respond(
                student_input or "I need guidance",
                case_context,
            )
            messages.append(senior_response)

        # Store in history
        if student_input:
            session.message_history.append({
                "agent_type": "student",
                "display_name": "You",
                "content": student_input,
            })
        session.message_history.extend(messages)

        return {
            "session_id": session_id,
            "messages": messages,
            "vitals": session.get_vitals(),
        }

    def get_session_vitals(self, session_id: str) -> Optional[dict]:
        """Get current vitals for a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        return session.get_vitals()

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get an agent session by ID."""
        return self.sessions.get(session_id)


# Singleton orchestrator shared across the app
orchestrator = AgentOrchestrator()
