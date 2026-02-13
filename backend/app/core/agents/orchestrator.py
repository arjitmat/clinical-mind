"""Agent orchestrator — coordinates the complete hospital simulation.

This is the BRAIN of the simulation:
- Manages sessions with full case state (time, vitals, investigations, treatments)
- Routes student actions through safety validation → treatment engine → agents
- Enables multi-agent interaction (agents respond to each other, not just student)
- Generates simulation events (lab results arriving, vitals changing, patient deteriorating)
- Provides state context to each agent so they're aware of the full picture
"""

import logging
import uuid
from typing import Optional

from app.core.agents.patient_agent import PatientAgent
from app.core.agents.nurse_agent import NurseAgent
from app.core.agents.senior_agent import SeniorDoctorAgent
from app.core.agents.knowledge_builder import knowledge_builder
from app.core.agents.case_state_manager import CaseStateManager
from app.core.agents.treatment_engine import treatment_engine
from app.core.agents.clinical_validator import clinical_validator

logger = logging.getLogger(__name__)


class AgentSession:
    """Holds the complete simulation state for a single case session."""

    def __init__(self, session_id: str, case_data: dict, student_level: str = "intern"):
        self.session_id = session_id
        self.case_data = case_data
        self.student_level = student_level

        # Initialize agents
        self.patient = PatientAgent()
        self.nurse = NurseAgent()
        self.senior = SeniorDoctorAgent()

        # Configure agents with case data
        self.patient.configure(case_data)
        self.nurse.configure(case_data)
        self.senior.configure(case_data)

        # Build dynamic knowledge — each agent specializes for this case
        self._build_agent_knowledge(case_data)

        # Initialize case state manager — time, vitals, investigations
        self.state = CaseStateManager(case_data, student_level)

        # Conversation tracking
        self.message_history: list[dict] = []
        self.diagnosis_submitted = False

    def _build_agent_knowledge(self, case_data: dict):
        """Use DynamicKnowledgeBuilder to specialize each agent for this case."""
        for role, agent, label in [
            ("patient", self.patient, "Patient"),
            ("nurse", self.nurse, "Nurse"),
            ("senior_doctor", self.senior, "Senior Doctor"),
        ]:
            try:
                knowledge = knowledge_builder.build_knowledge(case_data, role)
                agent.set_specialized_knowledge(knowledge)
                logger.info(f"{label} agent specialized for case ({len(knowledge)} chars)")
            except Exception as e:
                logger.warning(f"{label} knowledge build failed: {e}")

    def get_enriched_context(self) -> dict:
        """Build context dict enriched with current simulation state.

        This is passed to agents so they're aware of:
        - Current vitals (which may have changed from baseline)
        - Elapsed time
        - Pending investigations
        - Treatments administered
        - Patient trajectory
        """
        state_summary = self.state.get_state_summary()

        return {
            "chief_complaint": self.case_data.get("chief_complaint", ""),
            "specialty": self.case_data.get("specialty", ""),
            "difficulty": self.case_data.get("difficulty", ""),
            "simulation_state": state_summary,
            "student_level": self.student_level,
        }

    def get_vitals(self) -> dict:
        """Return current vitals with trends and trajectory."""
        vitals_display = self.state.get_vitals_display()
        return {
            "vitals": {
                "bp": vitals_display["bp"],
                "hr": vitals_display["hr"],
                "rr": vitals_display["rr"],
                "temp": vitals_display["temp"],
                "spo2": vitals_display["spo2"],
            },
            "trends": vitals_display.get("trends", {}),
            "trajectory": vitals_display["trajectory"],
            "elapsed_minutes": vitals_display["elapsed_minutes"],
            "urgency_level": self.nurse.urgency_level,
            "patient_distress": self.patient.distress_level,
        }


class AgentOrchestrator:
    """Coordinates all hospital agents for realistic multi-agent simulation."""

    def __init__(self):
        self.sessions: dict[str, AgentSession] = {}

    def initialize_session(
        self,
        case_data: dict,
        student_level: str = "intern",
        hospital_setting: str = "medical_college",
    ) -> dict:
        """Create a new simulation session.

        Returns initial messages from all agents + simulation state.
        """
        session_id = str(uuid.uuid4())[:8]
        session = AgentSession(session_id, case_data, student_level)
        self.sessions[session_id] = session

        initial_messages = []

        # 1. Nurse gives triage report (she sees the patient first)
        nurse_report = session.nurse.get_initial_report()
        initial_messages.append(nurse_report)

        # 2. Patient presents their complaint
        patient_greeting = session.patient.get_initial_greeting()
        initial_messages.append(patient_greeting)

        # 3. Senior doctor sets the teaching context
        senior_guidance = session.senior.get_initial_guidance()
        initial_messages.append(senior_guidance)

        session.message_history.extend(initial_messages)

        return {
            "session_id": session_id,
            "messages": initial_messages,
            "vitals": session.get_vitals(),
            "timeline": session.state.get_timeline(),
            "investigations": session.state.get_investigation_status(),
        }

    def process_action(
        self,
        session_id: str,
        action_type: str,
        student_input: Optional[str] = None,
    ) -> dict:
        """Process a student action through the complete simulation pipeline.

        Pipeline:
        1. Validate action for clinical safety
        2. Advance simulation clock
        3. Route to appropriate agent(s)
        4. Process treatment effects (if treatment)
        5. Check for triggered events
        6. Return responses + updated state
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found", "messages": []}

        messages = []
        context = session.get_enriched_context()

        # Step 1: Safety validation (for treatments and investigations)
        if action_type in ("order_treatment", "order_investigation") and student_input:
            validation = clinical_validator.validate_action(
                student_action=student_input,
                action_type=action_type,
                case_data=session.case_data,
                current_vitals=session.state.current_vitals,
                existing_treatments=[
                    {"description": tx.description} for tx in session.state.treatments
                ],
            )

            # If dangerous, agents intervene
            if validation["safety_level"] == "dangerous":
                if validation.get("nurse_intervention"):
                    messages.append({
                        "agent_type": "nurse",
                        "display_name": "Nurse Priya",
                        "content": validation["nurse_intervention"],
                        "urgency_level": "urgent",
                        "is_intervention": True,
                    })
                if validation.get("senior_intervention"):
                    messages.append({
                        "agent_type": "senior_doctor",
                        "display_name": "Dr. Sharma",
                        "content": validation["senior_intervention"],
                        "is_intervention": True,
                    })
                if validation.get("teaching_point"):
                    messages.append({
                        "agent_type": "senior_doctor",
                        "display_name": "Dr. Sharma",
                        "content": f"Teaching point: {validation['teaching_point']}",
                        "is_teaching": True,
                    })

                # Don't proceed with the dangerous action
                if not validation.get("proceed", True):
                    self._store_messages(session, student_input, messages)
                    return self._build_response(session, messages)

            elif validation["safety_level"] == "caution" and validation.get("nurse_intervention"):
                messages.append({
                    "agent_type": "nurse",
                    "display_name": "Nurse Priya",
                    "content": validation["nurse_intervention"],
                    "urgency_level": "attention",
                    "is_intervention": True,
                })

        # Step 2: Advance simulation clock
        triggered_events = session.state.advance_time(action_type)

        # Step 3: Route action to agents
        agent_responses = self._route_action(session, action_type, student_input, context)
        messages.extend(agent_responses)

        # Step 4: Process treatment (if treatment action)
        if action_type == "order_treatment" and student_input:
            treatment_msgs = self._process_treatment(session, student_input)
            messages.extend(treatment_msgs)

        # Step 5: Process investigation order
        if action_type == "order_investigation" and student_input:
            inv_messages = self._process_investigation(session, student_input)
            messages.extend(inv_messages)

        # Step 6: Deliver triggered events as agent messages
        for event in triggered_events:
            if not event.delivered:
                event.delivered = True
                messages.append({
                    "agent_type": event.agent_type or "nurse",
                    "display_name": "Nurse Priya" if event.agent_type == "nurse" else "Dr. Sharma",
                    "content": event.description,
                    "event_type": event.event_type,
                    "is_event": True,
                })

        # Step 7: Store and return
        self._store_messages(session, student_input, messages)
        return self._build_response(session, messages)

    def _route_action(
        self,
        session: AgentSession,
        action_type: str,
        student_input: Optional[str],
        context: dict,
    ) -> list[dict]:
        """Route a student action to the appropriate agent(s)."""
        messages = []
        enriched_input = student_input or ""

        if action_type == "talk_to_patient":
            resp = session.patient.respond(
                enriched_input or "Tell me about your problem",
                context,
            )
            messages.append(resp)

        elif action_type == "ask_nurse":
            resp = session.nurse.respond(
                enriched_input or "What are the current vitals?",
                context,
            )
            messages.append(resp)

        elif action_type == "consult_senior":
            resp = session.senior.respond(
                enriched_input or "What do you think about this case?",
                context,
            )
            messages.append(resp)

        elif action_type == "examine_patient":
            # Physical examination — patient reacts, nurse assists
            patient_resp = session.patient.respond(
                f"The doctor is examining you. {enriched_input or 'General examination.'}",
                context,
            )
            messages.append(patient_resp)

            nurse_resp = session.nurse.respond(
                f"Assisting with examination. Student is examining: {enriched_input or 'general exam'}. Report relevant findings from the case.",
                context,
            )
            messages.append(nurse_resp)

        elif action_type == "team_huddle":
            # ALL agents contribute — this is the multi-agent interaction
            nurse_resp = session.nurse.respond(
                f"Team huddle called. Report current patient status, pending investigations, and any concerns. Student's question: {enriched_input or 'Let us discuss the case.'}",
                context,
            )
            messages.append(nurse_resp)

            patient_resp = session.patient.respond(
                "The doctors are discussing your case. Is there anything new you want to tell them?",
                context,
            )
            messages.append(patient_resp)

            senior_resp = session.senior.respond(
                f"Team huddle. Nurse has reported: {nurse_resp.get('content', '')[:200]}. "
                f"Student asks: {enriched_input or 'What should we focus on?'}. "
                "Guide the student based on current case progress.",
                context,
            )
            messages.append(senior_resp)

        elif action_type in ("order_treatment", "order_investigation"):
            # Handled separately in process_action
            pass

        else:
            # Default: route to senior
            resp = session.senior.respond(
                enriched_input or "I need guidance on what to do next.",
                context,
            )
            messages.append(resp)

        return messages

    def _process_treatment(self, session: AgentSession, treatment_description: str) -> list[dict]:
        """Process a treatment order through the treatment engine."""
        messages = []

        assessment = treatment_engine.assess_treatment(
            treatment_description=treatment_description,
            case_data=session.case_data,
            current_vitals=session.state.current_vitals,
            existing_treatments=[
                {"description": tx.description} for tx in session.state.treatments
            ],
            specialized_knowledge=session.nurse.specialized_knowledge,
        )

        # Record the treatment with its effects
        session.state.record_treatment(
            description=treatment_description,
            effects=assessment.get("vital_effects", {}),
            is_appropriate=assessment.get("is_appropriate", True),
            safety_note=assessment.get("reasoning", ""),
        )

        # Nurse acknowledges the treatment
        nurse_msg = assessment.get("nurse_response", f"Starting {treatment_description} as ordered.")
        messages.append({
            "agent_type": "nurse",
            "display_name": "Nurse Priya",
            "content": nurse_msg,
            "urgency_level": "routine",
        })

        # If monitoring is needed, nurse mentions it
        monitoring = assessment.get("monitoring")
        if monitoring and monitoring != "Continue routine monitoring.":
            messages.append({
                "agent_type": "nurse",
                "display_name": "Nurse Priya",
                "content": f"I'll monitor: {monitoring}",
                "urgency_level": "attention",
            })

        return messages

    def _process_investigation(self, session: AgentSession, investigation_description: str) -> list[dict]:
        """Process an investigation order."""
        messages = []

        inv_type = self._parse_investigation_type(investigation_description)
        is_urgent = any(w in investigation_description.lower() for w in ["urgent", "stat", "emergency", "immediately"])

        investigation = session.state.order_investigation(inv_type, is_urgent)

        eta_text = f"{investigation.turnaround} minutes" if investigation.turnaround < 60 else f"{investigation.turnaround // 60} hours"
        urgency_text = "URGENT — " if is_urgent else ""
        messages.append({
            "agent_type": "nurse",
            "display_name": "Nurse Priya",
            "content": (
                f"Noted, doctor. {urgency_text}{investigation.label} ordered. "
                f"Sample collection done. Expected turnaround: {eta_text}. "
                f"I'll inform you as soon as results are ready."
            ),
            "urgency_level": "routine",
        })

        return messages

    def _parse_investigation_type(self, description: str) -> str:
        """Parse investigation type from free-text description."""
        desc = description.lower().strip()

        mappings = {
            "cbc": "cbc", "complete blood count": "cbc", "blood count": "cbc", "hemogram": "cbc",
            "rft": "rft", "renal function": "rft", "kidney function": "rft", "creatinine": "rft", "urea": "rft",
            "lft": "lft", "liver function": "lft", "bilirubin": "lft", "sgpt": "lft", "sgot": "lft",
            "blood sugar": "blood_sugar", "rbs": "rbs", "random blood sugar": "rbs",
            "fbs": "fbs", "fasting blood sugar": "fbs",
            "abg": "abg", "arterial blood gas": "abg", "blood gas": "abg",
            "ecg": "ecg", "ekg": "ecg", "electrocardiogram": "ecg",
            "chest x-ray": "xray_chest", "cxr": "xray_chest", "chest xray": "xray_chest",
            "x-ray": "xray", "xray": "xray",
            "ultrasound": "ultrasound", "usg": "ultrasound", "sonography": "ultrasound",
            "echo": "echo", "echocardiography": "echo", "2d echo": "echo",
            "ct scan": "ct_scan", "ct": "ct_scan", "cect": "ct_scan",
            "mri": "mri",
            "troponin": "troponin", "trop i": "troponin", "trop t": "troponin",
            "d-dimer": "d_dimer", "d dimer": "d_dimer",
            "blood culture": "blood_culture",
            "urine routine": "urine_routine", "urine r/m": "urine_routine",
            "urine culture": "urine_culture",
            "electrolytes": "serum_electrolytes", "sodium": "serum_electrolytes", "potassium": "serum_electrolytes",
            "coagulation": "coagulation", "pt inr": "pt_inr", "pt/inr": "pt_inr",
            "thyroid": "thyroid", "tft": "thyroid", "tsh": "thyroid",
            "hba1c": "hba1c",
            "amylase": "amylase", "lipase": "lipase",
            "dengue": "dengue_ns1", "ns1": "dengue_ns1",
            "malaria": "malaria_smear", "mp": "malaria_smear", "peripheral smear": "malaria_smear",
            "widal": "widal",
            "hiv": "hiv", "hbsag": "hbsag", "hepatitis": "hbsag",
            "csf": "csf_analysis", "lumbar puncture": "csf_analysis",
            "blood group": "blood_group", "crossmatch": "crossmatch",
            "procalcitonin": "procalcitonin",
            "bnp": "bnp",
        }

        for keyword, inv_type in mappings.items():
            if keyword in desc:
                return inv_type

        return desc.replace(" ", "_")[:30]

    def _store_messages(self, session: AgentSession, student_input: Optional[str], messages: list[dict]):
        """Store messages in session history."""
        if student_input:
            session.message_history.append({
                "agent_type": "student",
                "display_name": "You",
                "content": student_input,
            })
        session.message_history.extend(messages)

    def _build_response(self, session: AgentSession, messages: list[dict]) -> dict:
        """Build the standard response payload."""
        return {
            "session_id": session.session_id,
            "messages": messages,
            "vitals": session.get_vitals(),
            "timeline": session.state.get_timeline(),
            "investigations": session.state.get_investigation_status(),
        }

    def process_team_huddle(self, session_id: str, student_input: Optional[str] = None) -> dict:
        """Trigger a team huddle — all agents discuss the case."""
        return self.process_action(session_id, "team_huddle", student_input)

    def advance_time(self, session_id: str, minutes: int = 30) -> dict:
        """Explicitly advance simulation time (e.g., 'wait for results')."""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found", "messages": []}

        messages = []

        # Advance in the state manager
        session.state.elapsed_minutes += minutes
        session.state._evolve_vitals(minutes)

        # Check for events
        events = session.state._check_investigations()
        events.extend(session.state._check_patient_events())

        # Record vitals
        session.state.vitals_history.append({
            "time": session.state.elapsed_minutes,
            **session.state.current_vitals,
        })

        # Deliver events
        for event in events:
            if not event.delivered:
                event.delivered = True
                messages.append({
                    "agent_type": event.agent_type or "nurse",
                    "display_name": "Nurse Priya" if event.agent_type == "nurse" else "Dr. Sharma",
                    "content": event.description,
                    "event_type": event.event_type,
                    "is_event": True,
                })

        # Nurse gives time update if no events happened
        if not messages:
            messages.append({
                "agent_type": "nurse",
                "display_name": "Nurse Priya",
                "content": f"Doctor, {minutes} minutes have passed. Patient vitals are stable. No new developments.",
                "urgency_level": "routine",
            })

        self._store_messages(session, None, messages)
        return self._build_response(session, messages)

    def get_session_vitals(self, session_id: str) -> Optional[dict]:
        """Get current vitals for a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        return session.get_vitals()

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get an agent session by ID."""
        return self.sessions.get(session_id)

    def get_investigation_status(self, session_id: str) -> Optional[list[dict]]:
        """Get investigation status for a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        return session.state.get_investigation_status()

    def get_timeline(self, session_id: str) -> Optional[list[dict]]:
        """Get simulation timeline for a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        return session.state.get_timeline()


# Singleton orchestrator shared across the app
orchestrator = AgentOrchestrator()
