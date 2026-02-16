"""Agent orchestrator — coordinates the complete hospital simulation.

This is the BRAIN of the simulation:
- Manages sessions with full case state (time, vitals, investigations, treatments)
- Routes student actions through safety validation -> treatment engine -> agents
- Enables multi-agent interaction (agents respond to each other, not just student)
- Generates simulation events (lab results arriving, vitals changing, patient deteriorating)
- Manages complication engine for probabilistic emergencies
- Includes Family agent (cultural context) and Lab Tech agent (investigation lifecycle)
"""

import logging
import random
import uuid
from typing import Optional

from app.core.agents.patient_agent import PatientAgent
from app.core.agents.nurse_agent import NurseAgent
from app.core.agents.senior_agent import SeniorDoctorAgent
from app.core.agents.family_agent import FamilyAgent
from app.core.agents.lab_tech_agent import LabTechAgent
from app.core.agents.knowledge_builder import knowledge_builder
from app.core.agents.case_state_manager import CaseStateManager
from app.core.agents.treatment_engine import treatment_engine
from app.core.agents.clinical_validator import clinical_validator
from app.core.agents.complication_engine import ComplicationEngine
from app.core.agents.response_optimizer import parallel_processor

logger = logging.getLogger(__name__)


class AgentSession:
    """Holds the complete simulation state for a single case session."""

    def __init__(self, session_id: str, case_data: dict, student_level: str = "intern"):
        self.session_id = session_id
        self.case_data = case_data
        self.student_level = student_level

        # Initialize all 5 agents
        self.patient = PatientAgent()
        self.nurse = NurseAgent()
        self.senior = SeniorDoctorAgent()
        self.family = FamilyAgent()
        self.lab_tech = LabTechAgent()

        # Configure agents with case data
        self.patient.configure(case_data)
        self.nurse.configure(case_data)
        self.senior.configure(case_data)
        self.family.configure(case_data)
        self.lab_tech.configure(case_data)

        # Build dynamic knowledge — each agent specializes for this case
        self._build_agent_knowledge(case_data)

        # Initialize case state manager — time, vitals, investigations
        self.state = CaseStateManager(case_data, student_level)

        # Initialize complication engine
        self.complication_engine = ComplicationEngine(case_data, self.state)

        # Conversation tracking
        self.message_history: list[dict] = []
        self.diagnosis_submitted = False

    def _build_agent_knowledge(self, case_data: dict):
        """Use DynamicKnowledgeBuilder to specialize ALL agents for this case in PARALLEL.

        This runs 5x faster than sequential building by using ThreadPoolExecutor.
        """
        try:
            # Build knowledge for all 5 agents in parallel!
            all_knowledge = knowledge_builder.build_all_agent_knowledge(case_data)

            # Apply the knowledge to each agent
            agent_mapping = {
                "patient": (self.patient, "Patient"),
                "nurse": (self.nurse, "Nurse"),
                "senior_doctor": (self.senior, "Senior Doctor"),
                "family": (self.family, "Family"),
                "lab_tech": (self.lab_tech, "Lab Tech"),
            }

            for role, (agent, label) in agent_mapping.items():
                knowledge = all_knowledge.get(role, "")
                if knowledge:
                    agent.set_specialized_knowledge(knowledge)
                    logger.info(f"{label} agent specialized for case ({len(knowledge)} chars)")
                else:
                    logger.warning(f"{label} knowledge not available, using base prompts")

        except Exception as e:
            logger.error(f"Parallel knowledge building failed: {e}")
            # Fallback to sequential if parallel fails
            logger.info("Falling back to sequential knowledge building...")
            for role, agent, label in [
                ("patient", self.patient, "Patient"),
                ("nurse", self.nurse, "Nurse"),
                ("senior_doctor", self.senior, "Senior Doctor"),
                ("family", self.family, "Family"),
                ("lab_tech", self.lab_tech, "Lab Tech"),
            ]:
                try:
                    knowledge = knowledge_builder.build_knowledge(case_data, role)
                    agent.set_specialized_knowledge(knowledge)
                    logger.info(f"{label} agent specialized for case ({len(knowledge)} chars)")
                except Exception as e:
                    logger.warning(f"{label} knowledge build failed: {e}")

    def get_enriched_context(self) -> dict:
        """Build context dict enriched with current simulation state."""
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
        """Create a new simulation session with all 5 agents.

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

        # 3. Family member provides context
        family_context = session.family.get_initial_context()
        initial_messages.append(family_context)

        # 4. Senior doctor sets the teaching context
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
        5. Check for complications (complication engine)
        6. Check for triggered events
        7. Return responses + updated state
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

        # Step 6: Check complication engine
        complication_events = session.complication_engine.check_complications(
            elapsed_minutes=session.state.elapsed_minutes,
            current_vitals=session.state.current_vitals,
            treatments=session.state.treatments,
            investigations=session.state.investigations,
        )
        for event in complication_events:
            if not event.delivered:
                event.delivered = True
                messages.append({
                    "agent_type": event.agent_type or "nurse",
                    "display_name": "Nurse Priya" if event.agent_type == "nurse" else "Dr. Sharma",
                    "content": event.description,
                    "event_type": event.event_type,
                    "is_event": True,
                    "urgency_level": "critical" if "critical" in event.event_type else "urgent",
                })

        # Step 7: Deliver triggered state events as agent messages
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

        # Store and return
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

        # Use parallel processing for actions involving multiple agents
        if action_type == "talk_to_patient":
            # Prepare agents to process in parallel
            agents_to_process = [(
                session.patient,
                enriched_input or "Tell me about your problem",
                context,
            )]

            # Family may interject (50% chance on patient conversations)
            if random.random() < 0.5:
                agents_to_process.append((
                    session.family,
                    f"The doctor is asking the patient: {enriched_input}. You may add context or interject.",
                    context,
                ))

            # Process in parallel if multiple agents
            if len(agents_to_process) > 1:
                messages = parallel_processor.process_agents_parallel(agents_to_process, max_workers=2)
            else:
                messages.append(session.patient.respond(agents_to_process[0][1], context))

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

        elif action_type == "talk_to_family":
            resp = session.family.respond(
                enriched_input or "Can you tell me about the patient's background?",
                context,
            )
            messages.append(resp)

        elif action_type == "ask_lab":
            resp = session.lab_tech.respond(
                enriched_input or "What is the status of the investigations?",
                context,
            )
            messages.append(resp)

        elif action_type == "examine_patient":
            # Parallel processing for patient and nurse during examination
            agents_to_process = [
                (
                    session.patient,
                    f"The doctor is examining you. {enriched_input or 'General examination.'}",
                    context,
                ),
                (
                    session.nurse,
                    f"Assisting with examination. Student is examining: {enriched_input or 'general exam'}. Report relevant findings from the case.",
                    context,
                ),
            ]

            messages = parallel_processor.process_agents_parallel(agents_to_process, max_workers=2)

            exam_data = self._extract_examination_findings(session, enriched_input)
            if exam_data:
                messages.append({
                    "agent_type": "system",
                    "display_name": "Examination",
                    "content": "Examination findings available",
                    "examination_findings": exam_data,
                    "is_event": True,
                    "event_type": "examination",
                })

        elif action_type == "team_huddle":
            # Team huddle involves multiple agents - process first 3 in parallel
            agents_to_process = [
                (
                    session.nurse,
                    f"Team huddle called. Report current patient status, pending investigations, and any concerns. Student's question: {enriched_input or 'Let us discuss the case.'}",
                    context,
                ),
                (
                    session.patient,
                    "The doctors are discussing your case. Is there anything new you want to tell them?",
                    context,
                ),
                (
                    session.family,
                    "The medical team is discussing your relative's case. Share any concerns.",
                    context,
                ),
            ]

            # Process first 3 agents in parallel
            parallel_messages = parallel_processor.process_agents_parallel(agents_to_process, max_workers=3)
            messages.extend(parallel_messages)

            # Senior doctor needs nurse's response, so process after
            nurse_content = parallel_messages[0].get('content', '')[:200] if parallel_messages else ""
            senior_resp = session.senior.respond(
                f"Team huddle. Nurse has reported: {nurse_content}. "
                f"Student asks: {enriched_input or 'What should we focus on?'}. "
                "Guide the student based on current case progress.",
                context,
            )
            messages.append(senior_resp)

        elif action_type in ("order_treatment", "order_investigation"):
            pass  # Handled separately in process_action

        else:
            resp = session.senior.respond(
                enriched_input or "I need guidance on what to do next.",
                context,
            )
            messages.append(resp)

        return messages

    def _extract_examination_findings(self, session: AgentSession, exam_request: str) -> Optional[dict]:
        """Extract structured examination findings from case data for the exam modal."""
        findings: dict = {}

        for stage in session.case_data.get("stages", []):
            if stage.get("stage") == "physical_exam":
                exam_text = stage.get("info", "")
                sections = {
                    "inspection": [],
                    "palpation": [],
                    "percussion": [],
                    "auscultation": [],
                    "special_tests": [],
                }

                current_section = "inspection"
                for line in exam_text.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    line_lower = line.lower()
                    if "inspection" in line_lower or "general" in line_lower or "look" in line_lower:
                        current_section = "inspection"
                    elif "palpat" in line_lower or "feel" in line_lower or "tender" in line_lower:
                        current_section = "palpation"
                    elif "percuss" in line_lower:
                        current_section = "percussion"
                    elif "auscult" in line_lower or "listen" in line_lower or "heart sound" in line_lower or "breath" in line_lower:
                        current_section = "auscultation"
                    elif "special" in line_lower or "test" in line_lower or "sign" in line_lower:
                        current_section = "special_tests"
                    sections[current_section].append(line)

                for key, lines in sections.items():
                    if lines:
                        findings[key] = "\n".join(lines)
                break

        if not findings:
            return None

        specialty = session.case_data.get("specialty", "")
        if specialty in ("cardiology", "respiratory"):
            findings["sounds"] = [
                {"label": "Heart sounds", "description": "Auscultation findings as described above"},
            ]
        if specialty == "dermatology":
            findings["images"] = [
                {"label": "Skin findings", "description": "Visual examination findings as described above"},
            ]

        return findings

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

        session.state.record_treatment(
            description=treatment_description,
            effects=assessment.get("vital_effects", {}),
            is_appropriate=assessment.get("is_appropriate", True),
            safety_note=assessment.get("reasoning", ""),
        )

        nurse_msg = assessment.get("nurse_response", f"Starting {treatment_description} as ordered.")
        messages.append({
            "agent_type": "nurse",
            "display_name": "Nurse Priya",
            "content": nurse_msg,
            "urgency_level": "routine",
        })

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

        lab_resp = session.lab_tech.respond(
            f"New investigation ordered: {investigation.label}. {'Mark as URGENT.' if is_urgent else 'Routine.'} Process this investigation.",
            session.get_enriched_context(),
        )
        messages.append(lab_resp)

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
            "rft": "rft", "renal function": "rft", "kidney function": "rft", "creatinine": "rft",
            "lft": "lft", "liver function": "lft", "bilirubin": "lft", "sgpt": "lft",
            "blood sugar": "blood_sugar", "rbs": "rbs", "fbs": "fbs",
            "abg": "abg", "arterial blood gas": "abg", "blood gas": "abg",
            "ecg": "ecg", "ekg": "ecg", "electrocardiogram": "ecg",
            "chest x-ray": "xray_chest", "cxr": "xray_chest", "chest xray": "xray_chest",
            "x-ray": "xray", "xray": "xray",
            "ultrasound": "ultrasound", "usg": "ultrasound",
            "echo": "echo", "echocardiography": "echo", "2d echo": "echo",
            "ct scan": "ct_scan", "ct": "ct_scan",
            "mri": "mri",
            "troponin": "troponin", "d-dimer": "d_dimer", "d dimer": "d_dimer",
            "blood culture": "blood_culture",
            "urine routine": "urine_routine", "urine culture": "urine_culture",
            "electrolytes": "serum_electrolytes", "sodium": "serum_electrolytes",
            "coagulation": "coagulation", "pt inr": "pt_inr", "pt/inr": "pt_inr",
            "thyroid": "thyroid", "tft": "thyroid", "tsh": "thyroid",
            "hba1c": "hba1c", "amylase": "amylase", "lipase": "lipase",
            "dengue": "dengue_ns1", "ns1": "dengue_ns1",
            "malaria": "malaria_smear", "peripheral smear": "malaria_smear",
            "widal": "widal", "hiv": "hiv", "hbsag": "hbsag",
            "csf": "csf_analysis", "lumbar puncture": "csf_analysis",
            "blood group": "blood_group", "crossmatch": "crossmatch",
            "procalcitonin": "procalcitonin", "bnp": "bnp",
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
            "complications_fired": session.complication_engine.get_fired_complications(),
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

        session.state.elapsed_minutes += minutes
        session.state._evolve_vitals(minutes)

        events = session.state._check_investigations()
        events.extend(session.state._check_patient_events())

        complication_events = session.complication_engine.check_complications(
            elapsed_minutes=session.state.elapsed_minutes,
            current_vitals=session.state.current_vitals,
            treatments=session.state.treatments,
            investigations=session.state.investigations,
        )

        session.state.vitals_history.append({
            "time": session.state.elapsed_minutes,
            **session.state.current_vitals,
        })

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

        for event in complication_events:
            if not event.delivered:
                event.delivered = True
                messages.append({
                    "agent_type": event.agent_type or "nurse",
                    "display_name": "Nurse Priya" if event.agent_type == "nurse" else "Dr. Sharma",
                    "content": event.description,
                    "event_type": event.event_type,
                    "is_event": True,
                    "urgency_level": "critical" if "critical" in event.event_type else "urgent",
                })

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


class SimulationOrchestrator:
    """Simplified orchestrator for the /api/simulation endpoints.

    Wraps case generation + simulation state management to provide
    the interface expected by simulation.py (start_simulation,
    process_student_message, complete_simulation, get_simulation).
    """

    def __init__(self):
        from app.core.rag.shared import case_generator
        from app.models.simulation import (
            SimulationState,
            PatientProfile,
            PatientGender,
            EmotionalState,
            RapportLevel,
            SimulationMessage,
            TutorFeedback,
            FeedbackType,
        )

        self._case_generator = case_generator
        self._simulations: dict[str, SimulationState] = {}

        # Store model refs for use in methods
        self._SimulationState = SimulationState
        self._PatientProfile = PatientProfile
        self._PatientGender = PatientGender
        self._EmotionalState = EmotionalState
        self._RapportLevel = RapportLevel
        self._SimulationMessage = SimulationMessage
        self._TutorFeedback = TutorFeedback
        self._FeedbackType = FeedbackType

    def start_simulation(self, specialty: str = "general_medicine", difficulty: str = "intermediate"):
        """Start a new patient simulation, returning a SimulationState."""
        case = self._case_generator.generate_case(specialty=specialty, difficulty=difficulty)
        case_id = case.get("id", str(uuid.uuid4())[:8])

        # Map case data to PatientProfile
        gender_raw = case.get("patient_gender", "male").lower()
        gender_map = {"male": self._PatientGender.MALE, "female": self._PatientGender.FEMALE,
                       "pregnant": self._PatientGender.PREGNANT}
        gender = gender_map.get(gender_raw, self._PatientGender.MALE)

        profile = self._PatientProfile(
            age=case.get("patient_age", 45),
            gender=gender,
            name=case.get("patient_name", "Patient"),
            chief_complaint=case.get("chief_complaint", ""),
            setting=case.get("setting", "OPD"),
            specialty=specialty,
            difficulty=difficulty,
            actual_diagnosis=case.get("diagnosis", "Unknown"),
            key_history_points=case.get("key_history", case.get("learning_points", [])),
            physical_exam_findings=case.get("physical_exam", {}),
        )

        initial_message = self._SimulationMessage(
            role="patient",
            content=case.get("initial_presentation", f"Doctor, {profile.chief_complaint}"),
            emotional_state=self._EmotionalState.CONCERNED,
        )

        sim = self._SimulationState(
            case_id=case_id,
            patient_profile=profile,
            emotional_state=self._EmotionalState.CONCERNED,
            rapport_level=self._RapportLevel.MODERATE,
            messages=[initial_message],
        )

        self._simulations[case_id] = sim
        return sim

    def process_student_message(self, case_id: str, student_message: str):
        """Process a student message and return the updated SimulationState."""
        sim = self._get_or_raise(case_id)

        # Record student message
        sim.messages.append(self._SimulationMessage(role="student", content=student_message))

        # Generate patient response using the agent orchestrator if possible
        patient_response = self._generate_patient_response(sim, student_message)

        sim.messages.append(self._SimulationMessage(
            role="patient",
            content=patient_response,
            emotional_state=sim.emotional_state,
        ))

        # Generate tutor feedback
        feedback_type, feedback_msg = self._evaluate_student_message(student_message)
        sim.tutor_feedback.append(self._TutorFeedback(type=feedback_type, message=feedback_msg))

        return sim

    def complete_simulation(self, case_id: str, diagnosis: str, reasoning: str):
        """Mark simulation as complete with student's diagnosis."""
        from datetime import datetime

        sim = self._get_or_raise(case_id)
        sim.student_diagnosis = diagnosis
        sim.student_reasoning = reasoning
        sim.completed_at = datetime.now()
        return sim

    def get_simulation(self, case_id: str):
        """Get simulation state by case_id."""
        return self._get_or_raise(case_id)

    def _get_or_raise(self, case_id: str):
        sim = self._simulations.get(case_id)
        if not sim:
            raise ValueError(f"Simulation {case_id} not found")
        return sim

    def _generate_patient_response(self, sim, student_message: str) -> str:
        """Generate a contextual patient response."""
        complaint = sim.patient_profile.chief_complaint
        name = sim.patient_profile.name

        open_ended_markers = ["tell me", "describe", "how", "what", "when", "where"]
        is_open = any(m in student_message.lower() for m in open_ended_markers)

        empathy_markers = ["understand", "worried", "difficult", "sorry", "must be"]
        shows_empathy = any(m in student_message.lower() for m in empathy_markers)

        if shows_empathy:
            if sim.rapport_level.value < 5:
                sim.rapport_level = self._RapportLevel(min(5, sim.rapport_level.value + 1))
            sim.emotional_state = self._EmotionalState.CALM
            return (
                f"Thank you doctor, that makes me feel better. "
                f"Actually, I also wanted to mention that the {complaint} has been getting worse at night."
            )

        if is_open:
            return (
                f"Doctor, the {complaint} started about 3-4 days ago. "
                f"First I thought it was nothing, tried some home remedies. "
                f"But it kept getting worse so my family brought me here."
            )

        return (
            f"Yes doctor, the {complaint} is still bothering me. "
            f"What do you think it could be?"
        )

    def _evaluate_student_message(self, message: str):
        """Simple heuristic evaluation of student communication."""
        empathy_markers = ["understand", "worried", "difficult", "sorry", "must be", "concern"]
        open_markers = ["tell me", "describe", "how do you", "what happened", "can you explain"]

        if any(m in message.lower() for m in empathy_markers):
            return self._FeedbackType.POSITIVE, "Good empathetic communication. This builds rapport."
        if any(m in message.lower() for m in open_markers):
            return self._FeedbackType.POSITIVE, "Nice open-ended question. This encourages the patient to share more."
        if message.strip().endswith("?") and len(message.split()) > 5:
            return self._FeedbackType.WARNING, "Consider using more open-ended questions to gather richer history."
        return self._FeedbackType.WARNING, "Try to build rapport with empathetic language before diving into clinical questions."
