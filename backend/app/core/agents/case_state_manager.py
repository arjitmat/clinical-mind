"""Case state manager — time progression, vitals evolution, investigation lifecycle.

This is what makes it a SIMULATION, not a chatbot:
- Simulation clock advances with each student action
- Vitals evolve based on condition trajectory + treatments
- Investigations have realistic turnaround times (Indian govt hospital)
- Patient state can improve or deteriorate based on management
"""

import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class PatientTrajectory(str, Enum):
    """Patient clinical trajectory."""
    STABLE = "stable"
    IMPROVING = "improving"
    DETERIORATING = "deteriorating"
    CRITICAL = "critical"


class InvestigationStatus(str, Enum):
    """Investigation lifecycle status."""
    ORDERED = "ordered"
    SAMPLE_COLLECTED = "sample_collected"
    PROCESSING = "processing"
    READY = "ready"
    DELIVERED = "delivered"


# Realistic turnaround times for Indian govt hospital (in simulation minutes)
INVESTIGATION_TURNAROUND = {
    # Basic labs — available in most govt hospitals
    "cbc": {"turnaround": 120, "urgent": 30, "label": "Complete Blood Count"},
    "rft": {"turnaround": 150, "urgent": 45, "label": "Renal Function Test"},
    "lft": {"turnaround": 150, "urgent": 45, "label": "Liver Function Test"},
    "blood_sugar": {"turnaround": 30, "urgent": 10, "label": "Blood Sugar (Random)"},
    "rbs": {"turnaround": 30, "urgent": 10, "label": "Random Blood Sugar"},
    "fbs": {"turnaround": 30, "urgent": 10, "label": "Fasting Blood Sugar"},
    "urine_routine": {"turnaround": 60, "urgent": 20, "label": "Urine Routine/Microscopy"},
    "serum_electrolytes": {"turnaround": 120, "urgent": 30, "label": "Serum Electrolytes"},
    "abg": {"turnaround": 20, "urgent": 10, "label": "Arterial Blood Gas"},
    "hba1c": {"turnaround": 180, "urgent": 60, "label": "HbA1c"},
    "coagulation": {"turnaround": 120, "urgent": 30, "label": "PT/INR/aPTT"},
    "pt_inr": {"turnaround": 120, "urgent": 30, "label": "PT/INR"},
    "blood_group": {"turnaround": 30, "urgent": 15, "label": "Blood Group & Rh"},
    "crossmatch": {"turnaround": 60, "urgent": 30, "label": "Crossmatch"},

    # Special labs — may need special request
    "troponin": {"turnaround": 90, "urgent": 30, "label": "Troponin I/T"},
    "d_dimer": {"turnaround": 120, "urgent": 45, "label": "D-Dimer"},
    "bnp": {"turnaround": 120, "urgent": 45, "label": "BNP/NT-proBNP"},
    "procalcitonin": {"turnaround": 180, "urgent": 60, "label": "Procalcitonin"},
    "blood_culture": {"turnaround": 2880, "urgent": 2880, "label": "Blood Culture (Prelim 24h, Final 48h)"},
    "urine_culture": {"turnaround": 2880, "urgent": 2880, "label": "Urine Culture"},
    "csf_analysis": {"turnaround": 120, "urgent": 45, "label": "CSF Analysis"},
    "amylase": {"turnaround": 120, "urgent": 30, "label": "Serum Amylase"},
    "lipase": {"turnaround": 120, "urgent": 30, "label": "Serum Lipase"},
    "thyroid": {"turnaround": 240, "urgent": 120, "label": "Thyroid Profile (T3/T4/TSH)"},

    # Serology
    "dengue_ns1": {"turnaround": 60, "urgent": 30, "label": "Dengue NS1 Antigen"},
    "dengue_serology": {"turnaround": 120, "urgent": 60, "label": "Dengue IgM/IgG"},
    "malaria_smear": {"turnaround": 60, "urgent": 20, "label": "Peripheral Smear for MP"},
    "malaria_rdt": {"turnaround": 15, "urgent": 10, "label": "Malaria Rapid Test"},
    "widal": {"turnaround": 120, "urgent": 60, "label": "Widal Test"},
    "hiv": {"turnaround": 60, "urgent": 30, "label": "HIV Rapid/ELISA"},
    "hbsag": {"turnaround": 60, "urgent": 30, "label": "HBsAg"},
    "anti_hcv": {"turnaround": 60, "urgent": 30, "label": "Anti-HCV"},

    # Imaging — availability varies
    "xray_chest": {"turnaround": 30, "urgent": 15, "label": "Chest X-ray PA"},
    "xray": {"turnaround": 30, "urgent": 15, "label": "X-ray"},
    "ecg": {"turnaround": 15, "urgent": 5, "label": "12-lead ECG"},
    "ultrasound": {"turnaround": 120, "urgent": 30, "label": "USG Abdomen (needs radiology call)"},
    "echo": {"turnaround": 240, "urgent": 60, "label": "2D Echocardiography"},
    "ct_scan": {"turnaround": 480, "urgent": 120, "label": "CT Scan (may need referral)"},
    "mri": {"turnaround": 1440, "urgent": 480, "label": "MRI (usually needs referral)"},

    # Default for unrecognized
    "_default": {"turnaround": 180, "urgent": 60, "label": "Investigation"},
}

# Time cost per student action (simulation minutes)
ACTION_TIME_COST = {
    "talk_to_patient": 10,
    "ask_nurse": 5,
    "consult_senior": 10,
    "examine_patient": 15,
    "order_investigation": 5,
    "order_treatment": 5,
    "team_huddle": 15,
    "wait_for_results": 30,
    "review_results": 5,
}


@dataclass
class OrderedInvestigation:
    """Tracks a single ordered investigation."""
    investigation_id: str
    investigation_type: str
    label: str
    ordered_at: int  # simulation minute
    turnaround: int  # minutes until ready
    status: InvestigationStatus = InvestigationStatus.ORDERED
    result_text: str = ""  # populated from case data when ready
    is_urgent: bool = False


@dataclass
class TreatmentRecord:
    """Tracks a treatment ordered by the student."""
    treatment_id: str
    description: str
    ordered_at: int
    effects: dict = field(default_factory=dict)
    is_appropriate: bool = True
    safety_note: str = ""


@dataclass
class SimulationEvent:
    """A timed event in the simulation."""
    event_id: str
    timestamp: int  # simulation minute
    event_type: str  # "investigation_ready", "vitals_change", "patient_event", "nurse_alert"
    title: str
    description: str
    agent_type: str = ""  # which agent delivers this
    delivered: bool = False


class CaseStateManager:
    """Manages the complete simulation state for a case session.

    Tracks:
    - Simulation clock (elapsed minutes)
    - Vital signs with evolution
    - Investigation orders and lifecycle
    - Treatment log
    - Patient trajectory
    - Timed simulation events
    """

    def __init__(self, case_data: dict, student_level: str = "intern"):
        self.case_data = case_data
        self.student_level = student_level

        # Simulation clock
        self.elapsed_minutes: int = 0
        self.action_count: int = 0

        # Vitals — start from case data, evolve over time
        vitals = case_data.get("vital_signs", {})
        self.current_vitals: dict = {
            "bp_systolic": self._parse_bp(vitals.get("bp", "120/80"), "systolic"),
            "bp_diastolic": self._parse_bp(vitals.get("bp", "120/80"), "diastolic"),
            "hr": int(vitals.get("hr", 80)),
            "rr": int(vitals.get("rr", 16)),
            "temp": float(vitals.get("temp", 37.0)),
            "spo2": int(vitals.get("spo2", 98)),
        }
        self.baseline_vitals: dict = self.current_vitals.copy()
        self.vitals_history: list[dict] = [
            {"time": 0, **self.current_vitals}
        ]

        # Patient trajectory
        self.trajectory: PatientTrajectory = self._initial_trajectory()

        # Investigation tracking
        self.investigations: dict[str, OrderedInvestigation] = {}
        self._next_inv_id: int = 0

        # Treatment log
        self.treatments: list[TreatmentRecord] = []

        # Simulation events queue
        self.events: list[SimulationEvent] = []
        self._next_event_id: int = 0

        # Extract investigation results from case data for realistic delivery
        self._case_lab_data = self._extract_lab_data(case_data)

    def _parse_bp(self, bp_str: str, component: str) -> int:
        """Parse BP string like '120/80' into systolic or diastolic."""
        try:
            parts = str(bp_str).split("/")
            if component == "systolic":
                return int(parts[0])
            return int(parts[1]) if len(parts) > 1 else 80
        except (ValueError, IndexError):
            return 120 if component == "systolic" else 80

    def _initial_trajectory(self) -> PatientTrajectory:
        """Determine initial trajectory from case severity."""
        difficulty = self.case_data.get("difficulty", "intermediate")
        spo2 = self.current_vitals["spo2"]
        hr = self.current_vitals["hr"]

        if difficulty == "advanced" or spo2 < 90 or hr > 130:
            return PatientTrajectory.DETERIORATING
        if spo2 < 94 or hr > 110:
            return PatientTrajectory.STABLE  # at risk but stable initially
        return PatientTrajectory.STABLE

    def _extract_lab_data(self, case_data: dict) -> str:
        """Extract lab/investigation data from case stages for result delivery."""
        for stage in case_data.get("stages", []):
            if stage.get("stage") == "labs":
                return stage.get("info", "")
        return ""

    def advance_time(self, action_type: str) -> list[SimulationEvent]:
        """Advance the simulation clock and return any triggered events.

        Called after each student action. Returns events that should be delivered.
        """
        time_cost = ACTION_TIME_COST.get(action_type, 10)
        self.elapsed_minutes += time_cost
        self.action_count += 1

        triggered_events: list[SimulationEvent] = []

        # 1. Evolve vitals
        self._evolve_vitals(time_cost)

        # 2. Check investigation status
        triggered_events.extend(self._check_investigations())

        # 3. Check for patient state events
        triggered_events.extend(self._check_patient_events())

        # 4. Record vitals snapshot
        self.vitals_history.append({
            "time": self.elapsed_minutes,
            **self.current_vitals,
        })

        return triggered_events

    def _evolve_vitals(self, minutes_passed: int):
        """Evolve vital signs based on trajectory and time.

        Changes are subtle and clinically realistic — not random noise.
        """
        v = self.current_vitals

        if self.trajectory == PatientTrajectory.DETERIORATING:
            # Gradual worsening — clinically realistic
            rate = minutes_passed / 60  # fraction of an hour
            v["hr"] = min(180, v["hr"] + int(3 * rate + random.uniform(0, 2)))
            v["rr"] = min(45, v["rr"] + int(2 * rate + random.uniform(0, 1)))
            v["spo2"] = max(70, v["spo2"] - int(1 * rate + random.uniform(0, 1)))
            v["bp_systolic"] = max(60, v["bp_systolic"] - int(2 * rate))
            v["temp"] = min(41.0, v["temp"] + 0.1 * rate)

        elif self.trajectory == PatientTrajectory.IMPROVING:
            # Gradual improvement toward normal
            rate = minutes_passed / 60
            target_hr = 80
            target_rr = 16
            target_spo2 = 98
            target_bp = 120
            target_temp = 37.0

            v["hr"] = v["hr"] + int((target_hr - v["hr"]) * 0.1 * rate)
            v["rr"] = v["rr"] + int((target_rr - v["rr"]) * 0.1 * rate)
            v["spo2"] = min(100, v["spo2"] + int((target_spo2 - v["spo2"]) * 0.1 * rate))
            v["bp_systolic"] = v["bp_systolic"] + int((target_bp - v["bp_systolic"]) * 0.1 * rate)
            v["temp"] = v["temp"] + (target_temp - v["temp"]) * 0.1 * rate

        elif self.trajectory == PatientTrajectory.CRITICAL:
            # Rapid deterioration
            rate = minutes_passed / 30
            v["hr"] = min(200, v["hr"] + int(5 * rate))
            v["rr"] = min(50, v["rr"] + int(3 * rate))
            v["spo2"] = max(60, v["spo2"] - int(3 * rate))
            v["bp_systolic"] = max(50, v["bp_systolic"] - int(5 * rate))

        # STABLE: very minor fluctuation only
        elif self.trajectory == PatientTrajectory.STABLE:
            v["hr"] += random.choice([-1, 0, 0, 1])
            v["rr"] += random.choice([-1, 0, 0, 0, 1])

        # Clamp values
        v["hr"] = max(30, min(200, v["hr"]))
        v["rr"] = max(6, min(50, v["rr"]))
        v["spo2"] = max(60, min(100, v["spo2"]))
        v["bp_systolic"] = max(50, min(220, v["bp_systolic"]))
        v["bp_diastolic"] = max(30, min(130, v["bp_diastolic"]))
        v["temp"] = round(max(35.0, min(42.0, v["temp"])), 1)

    def _check_investigations(self) -> list[SimulationEvent]:
        """Check if any ordered investigations are now ready."""
        events = []
        for inv_id, inv in self.investigations.items():
            if inv.status in (InvestigationStatus.ORDERED, InvestigationStatus.SAMPLE_COLLECTED, InvestigationStatus.PROCESSING):
                time_since_order = self.elapsed_minutes - inv.ordered_at
                if time_since_order >= inv.turnaround:
                    inv.status = InvestigationStatus.READY
                    event = SimulationEvent(
                        event_id=f"evt-{self._next_event_id}",
                        timestamp=self.elapsed_minutes,
                        event_type="investigation_ready",
                        title=f"{inv.label} Results Ready",
                        description=inv.result_text or f"{inv.label} results are now available.",
                        agent_type="nurse",
                    )
                    self._next_event_id += 1
                    events.append(event)
                    self.events.append(event)
                elif time_since_order >= inv.turnaround * 0.5 and inv.status == InvestigationStatus.ORDERED:
                    inv.status = InvestigationStatus.PROCESSING
        return events

    def _check_patient_events(self) -> list[SimulationEvent]:
        """Generate patient-state-driven events (deterioration alerts, new symptoms)."""
        events = []
        v = self.current_vitals

        # Critical vitals trigger nurse alert
        if v["spo2"] < 88 and not self._event_delivered("critical_spo2"):
            event = SimulationEvent(
                event_id=f"evt-{self._next_event_id}",
                timestamp=self.elapsed_minutes,
                event_type="nurse_alert",
                title="Critical SpO2 Alert",
                description=f"Doctor! Patient's SpO2 has dropped to {v['spo2']}%. Should we start high-flow O2?",
                agent_type="nurse",
            )
            self._next_event_id += 1
            events.append(event)
            self.events.append(event)

        if v["hr"] > 140 and not self._event_delivered("tachycardia_alert"):
            event = SimulationEvent(
                event_id=f"evt-{self._next_event_id}",
                timestamp=self.elapsed_minutes,
                event_type="nurse_alert",
                title="Tachycardia Alert",
                description=f"Doctor, HR is {v['hr']}. Patient is becoming restless. Do you want ECG monitoring?",
                agent_type="nurse",
            )
            self._next_event_id += 1
            events.append(event)
            self.events.append(event)

        if v["bp_systolic"] < 80 and not self._event_delivered("hypotension_alert"):
            event = SimulationEvent(
                event_id=f"evt-{self._next_event_id}",
                timestamp=self.elapsed_minutes,
                event_type="nurse_alert",
                title="Hypotension Alert",
                description=f"Doctor! BP is {v['bp_systolic']}/{v['bp_diastolic']}. Patient is hypotensive. Should I start IV fluids?",
                agent_type="nurse",
            )
            self._next_event_id += 1
            events.append(event)
            self.events.append(event)

        # Time-based deterioration warning (if no treatment after 30 min of deterioration)
        if (
            self.trajectory == PatientTrajectory.DETERIORATING
            and self.elapsed_minutes > 30
            and len(self.treatments) == 0
            and not self._event_delivered("no_treatment_warning")
        ):
            event = SimulationEvent(
                event_id=f"evt-{self._next_event_id}",
                timestamp=self.elapsed_minutes,
                event_type="senior_concern",
                title="Senior Doctor Concern",
                description="The patient has been here for a while without treatment. Have we started any management?",
                agent_type="senior_doctor",
            )
            self._next_event_id += 1
            events.append(event)
            self.events.append(event)

        return events

    def _event_delivered(self, event_key: str) -> bool:
        """Check if a named event has already been triggered."""
        return any(
            e.event_id.endswith(event_key) or event_key in e.title.lower().replace(" ", "_")
            for e in self.events
        )

    def order_investigation(
        self, investigation_type: str, is_urgent: bool = False
    ) -> OrderedInvestigation:
        """Order an investigation. Returns the tracking object."""
        inv_type_key = investigation_type.lower().replace(" ", "_").replace("-", "_")

        # Match against known investigations
        inv_info = INVESTIGATION_TURNAROUND.get(inv_type_key, INVESTIGATION_TURNAROUND["_default"])
        turnaround = inv_info["urgent"] if is_urgent else inv_info["turnaround"]

        inv_id = f"inv-{self._next_inv_id}"
        self._next_inv_id += 1

        investigation = OrderedInvestigation(
            investigation_id=inv_id,
            investigation_type=inv_type_key,
            label=inv_info["label"],
            ordered_at=self.elapsed_minutes,
            turnaround=turnaround,
            is_urgent=is_urgent,
            result_text=self._get_investigation_result(inv_type_key),
        )
        self.investigations[inv_id] = investigation

        logger.info(
            f"Investigation ordered: {investigation.label} "
            f"(ETA: {turnaround}min, urgent={is_urgent})"
        )
        return investigation

    def _get_investigation_result(self, inv_type: str) -> str:
        """Extract relevant result text from case data for this investigation type.

        Uses Claude-style pattern matching on the case lab data to find relevant results.
        """
        if not self._case_lab_data:
            return f"{inv_type.upper()} results: Within normal limits."

        # Simple keyword matching against case lab text
        lab_text = self._case_lab_data.lower()
        inv_keywords = {
            "cbc": ["cbc", "hemoglobin", "hb ", "wbc", "platelet", "tlc", "dlc"],
            "rft": ["creatinine", "urea", "bun", "egfr", "rft", "renal"],
            "lft": ["bilirubin", "sgot", "sgpt", "alt", "ast", "lft", "albumin", "liver"],
            "blood_sugar": ["blood sugar", "glucose", "rbs", "fbs"],
            "rbs": ["blood sugar", "glucose", "rbs"],
            "abg": ["abg", "arterial blood gas", "pao2", "pco2", "ph ", "bicarbonate", "hco3"],
            "troponin": ["troponin", "trop"],
            "ecg": ["ecg", "electrocardiogram", "st elevation", "st depression", "qrs", "rhythm"],
            "xray_chest": ["x-ray", "xray", "chest x", "cxr", "infiltrate", "consolidation"],
            "xray": ["x-ray", "xray"],
            "ultrasound": ["usg", "ultrasound", "sonography"],
            "dengue_ns1": ["ns1", "dengue"],
            "dengue_serology": ["dengue igm", "dengue igg"],
            "malaria_smear": ["peripheral smear", "malaria", "mp"],
            "malaria_rdt": ["malaria rapid", "rdt"],
            "blood_culture": ["blood culture", "bacteremia"],
            "serum_electrolytes": ["sodium", "potassium", "electrolyte", "na+", "k+"],
            "coagulation": ["pt ", "inr", "aptt", "coagulation"],
            "pt_inr": ["pt ", "inr"],
            "thyroid": ["tsh", "t3", "t4", "thyroid"],
            "hba1c": ["hba1c", "glycated"],
            "amylase": ["amylase"],
            "lipase": ["lipase"],
            "csf_analysis": ["csf", "cerebrospinal"],
            "d_dimer": ["d-dimer", "d dimer"],
            "echo": ["echo", "echocardiography", "ef ", "ejection fraction", "lvef"],
        }

        keywords = inv_keywords.get(inv_type, [inv_type])
        relevant_lines = []

        for line in self._case_lab_data.split("\n"):
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                relevant_lines.append(line.strip())

        if relevant_lines:
            return "\n".join(relevant_lines)

        return f"{inv_type.replace('_', ' ').title()}: Results within normal limits (no specific abnormality noted)."

    def record_treatment(
        self,
        description: str,
        effects: dict,
        is_appropriate: bool = True,
        safety_note: str = "",
    ) -> TreatmentRecord:
        """Record a treatment and apply its effects to vitals."""
        record = TreatmentRecord(
            treatment_id=f"tx-{len(self.treatments)}",
            description=description,
            ordered_at=self.elapsed_minutes,
            effects=effects,
            is_appropriate=is_appropriate,
            safety_note=safety_note,
        )
        self.treatments.append(record)

        # Apply immediate effects to vitals
        self._apply_treatment_effects(effects, is_appropriate)

        return record

    def _apply_treatment_effects(self, effects: dict, is_appropriate: bool):
        """Apply treatment effects to current vitals and trajectory."""
        if is_appropriate:
            # Correct treatment shifts trajectory toward improving
            if self.trajectory in (PatientTrajectory.DETERIORATING, PatientTrajectory.CRITICAL):
                self.trajectory = PatientTrajectory.STABLE
            elif self.trajectory == PatientTrajectory.STABLE:
                self.trajectory = PatientTrajectory.IMPROVING

            # Apply specific effects
            v = self.current_vitals
            if "hr_change" in effects:
                v["hr"] = max(40, min(180, v["hr"] + effects["hr_change"]))
            if "bp_systolic_change" in effects:
                v["bp_systolic"] = max(60, min(200, v["bp_systolic"] + effects["bp_systolic_change"]))
            if "spo2_change" in effects:
                v["spo2"] = min(100, max(60, v["spo2"] + effects["spo2_change"]))
            if "rr_change" in effects:
                v["rr"] = max(8, min(40, v["rr"] + effects["rr_change"]))
            if "temp_change" in effects:
                v["temp"] = round(max(35.0, min(42.0, v["temp"] + effects["temp_change"])), 1)
        else:
            # Wrong treatment worsens trajectory
            if self.trajectory == PatientTrajectory.STABLE:
                self.trajectory = PatientTrajectory.DETERIORATING
            elif self.trajectory == PatientTrajectory.DETERIORATING:
                self.trajectory = PatientTrajectory.CRITICAL

    def get_vitals_display(self) -> dict:
        """Get current vitals formatted for display with trends."""
        v = self.current_vitals
        bp_str = f"{v['bp_systolic']}/{v['bp_diastolic']}"

        # Calculate trends by comparing to 2 snapshots ago
        trends = {}
        if len(self.vitals_history) >= 2:
            prev = self.vitals_history[-2]
            for key in ["hr", "rr", "spo2", "bp_systolic", "temp"]:
                diff = v[key] - prev[key]
                if isinstance(diff, float):
                    trends[key] = "rising" if diff > 0.2 else "falling" if diff < -0.2 else "stable"
                else:
                    trends[key] = "rising" if diff > 2 else "falling" if diff < -2 else "stable"

        return {
            "bp": bp_str,
            "hr": v["hr"],
            "rr": v["rr"],
            "temp": v["temp"],
            "spo2": v["spo2"],
            "trends": trends,
            "trajectory": self.trajectory.value,
            "elapsed_minutes": self.elapsed_minutes,
        }

    def get_investigation_status(self) -> list[dict]:
        """Get status of all ordered investigations."""
        results = []
        for inv in self.investigations.values():
            remaining = max(0, inv.turnaround - (self.elapsed_minutes - inv.ordered_at))
            results.append({
                "id": inv.investigation_id,
                "type": inv.investigation_type,
                "label": inv.label,
                "status": inv.status.value,
                "ordered_at": inv.ordered_at,
                "estimated_ready": inv.ordered_at + inv.turnaround,
                "remaining_minutes": remaining,
                "is_urgent": inv.is_urgent,
                "result": inv.result_text if inv.status == InvestigationStatus.READY else None,
            })
        return results

    def get_timeline(self) -> list[dict]:
        """Get complete simulation timeline for display."""
        timeline = [
            {"time": 0, "type": "patient_arrival", "title": "Patient arrives", "description": self.case_data.get("chief_complaint", "")}
        ]

        # Add investigation orders
        for inv in self.investigations.values():
            timeline.append({
                "time": inv.ordered_at,
                "type": "investigation_ordered",
                "title": f"{inv.label} ordered",
                "description": f"{'Urgent' if inv.is_urgent else 'Routine'} — ETA {inv.turnaround} min",
            })
            if inv.status == InvestigationStatus.READY:
                timeline.append({
                    "time": inv.ordered_at + inv.turnaround,
                    "type": "investigation_ready",
                    "title": f"{inv.label} ready",
                    "description": "Results available",
                })

        # Add treatments
        for tx in self.treatments:
            timeline.append({
                "time": tx.ordered_at,
                "type": "treatment",
                "title": f"Treatment: {tx.description[:50]}",
                "description": tx.safety_note or "Treatment administered",
            })

        # Add simulation events
        for evt in self.events:
            timeline.append({
                "time": evt.timestamp,
                "type": evt.event_type,
                "title": evt.title,
                "description": evt.description,
            })

        # Sort by time
        timeline.sort(key=lambda x: x["time"])
        return timeline

    def get_state_summary(self) -> str:
        """Generate a natural-language summary of current state for agent context.

        This is injected into agent prompts so they're aware of what's happening.
        """
        v = self.current_vitals
        summary_parts = [
            f"SIMULATION TIME: {self.elapsed_minutes} minutes elapsed.",
            f"CURRENT VITALS: BP {v['bp_systolic']}/{v['bp_diastolic']}, HR {v['hr']}, RR {v['rr']}, Temp {v['temp']}°C, SpO2 {v['spo2']}%.",
            f"PATIENT TRAJECTORY: {self.trajectory.value}.",
        ]

        # Pending investigations
        pending = [inv for inv in self.investigations.values() if inv.status != InvestigationStatus.READY]
        ready = [inv for inv in self.investigations.values() if inv.status == InvestigationStatus.READY]
        if pending:
            summary_parts.append(f"PENDING INVESTIGATIONS: {', '.join(inv.label for inv in pending)}.")
        if ready:
            summary_parts.append(f"RESULTS AVAILABLE: {', '.join(inv.label for inv in ready)}.")

        # Treatments
        if self.treatments:
            recent = self.treatments[-3:]
            summary_parts.append(f"RECENT TREATMENTS: {'; '.join(tx.description for tx in recent)}.")
        else:
            summary_parts.append("NO TREATMENTS ORDERED YET.")

        return "\n".join(summary_parts)
