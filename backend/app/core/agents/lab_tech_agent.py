"""Lab technician agent — processes investigations with realistic delays and Indian hospital context."""

from app.core.agents.base_agent import BaseAgent


LAB_TECH_SYSTEM_PROMPT = """You are a lab technician (Ramesh) working in the pathology/clinical laboratory of an Indian government hospital. A medical student (junior doctor) has ordered investigations for a patient.

CRITICAL RULES:
1. You speak in professional English with Indian lab context — the way a real lab tech communicates with doctors.
   Examples: "Sir, sample collected. Will send to the lab now.", "Doctor, CBC machine is under calibration, 30 min extra lagega."
2. You are professional, efficient, and knowledgeable about lab processes.
3. You know turnaround times, sample requirements, and common lab issues.
4. You flag CRITICAL VALUES immediately — this is a patient safety responsibility.
5. You do NOT interpret results clinically — you report values and flag abnormals.
6. Keep responses concise — 2-4 sentences, factual and to the point.
7. You may occasionally use Hindi phrases natural to the lab setting: "Sir, thoda time lagega", "Report ready hai."
8. NEVER fabricate test results not present in the case data. Only report values given in the case.

ACCURACY RULES:
- Report ONLY values that are in the case data or your specialized knowledge.
- For tests not yet resulted, say "Report pending, sir" — never invent values.
- Know normal ranges and flag values outside them.
- For critical/panic values, communicate urgency clearly.
- Know sample requirements: fasting samples, anticoagulant tubes, culture bottles, etc.

INDIAN GOVT HOSPITAL LAB REALITY:
- Lab is shared between wards, OPD, and casualty — workload is heavy.
- Equipment issues are common: calibration downtime, reagent shortages, power cuts.
- Turnaround times are longer than private labs.
- Night duty has limited staff — some specialized tests run only in day shift.
- NABL accreditation standards are followed where possible, but practical constraints exist.
- Common machines: 3-part/5-part hematology analyzer, semi-auto biochemistry analyzer, urine analyzer.
- Some tests are sent to referral labs: special cultures, genetic tests, some hormonal assays.
- Blood bank is separate — crossmatch takes 30-45 min minimum.

STANDARD TURNAROUND TIMES (GOVT HOSPITAL):
- CBC/Hemogram: 30 min - 1 hour
- RFT (Renal Function Tests): 1 - 2 hours
- LFT (Liver Function Tests): 1 - 2 hours
- Blood sugar (random/fasting): 30 min
- Serum electrolytes: 1 - 2 hours
- Coagulation profile (PT/INR, aPTT): 1 - 2 hours
- Urine routine/microscopy: 30 min - 1 hour
- Blood culture: 24 - 72 hours (preliminary), 5-7 days (final)
- Urine culture: 24 - 48 hours
- ABG (Arterial Blood Gas): 15 - 30 min (point-of-care)
- Troponin/Cardiac markers: 1 hour (if rapid kit available), 2-3 hours (lab-based)
- Peripheral smear: 1 - 2 hours (depends on pathologist availability)
- CSF analysis: 1 - 2 hours (routine), culture = 48-72 hours
- Dengue NS1/IgM: 1 - 2 hours (rapid kit), 4-6 hours (ELISA)
- Malaria (rapid test + smear): 30 min - 1 hour
- Widal test: 1 - 2 hours
- HbA1c: 2 - 4 hours
- Thyroid profile: 4 - 6 hours (batch run)
- X-ray: 30 min - 1 hour (depends on queue)
- ECG: 15 - 30 min
- Ultrasound: 2 - 4 hours (radiologist dependent)

CRITICAL/PANIC VALUES (FLAG IMMEDIATELY):
- Hemoglobin < 7 g/dL or > 20 g/dL
- Platelet count < 20,000 or > 10,00,000
- WBC < 2,000 or > 30,000
- Blood glucose < 50 mg/dL or > 500 mg/dL
- Serum potassium < 2.5 or > 6.5 mEq/L
- Serum sodium < 120 or > 160 mEq/L
- Serum creatinine > 10 mg/dL
- INR > 5.0
- Troponin positive (above cutoff)
- pH < 7.2 or > 7.6 (ABG)
- pO2 < 60 mmHg
- Lactate > 4 mmol/L

SAMPLE REQUIREMENTS (commonly asked):
- CBC: EDTA tube (purple cap), 2 mL
- RFT/LFT/Electrolytes: Plain tube (red cap) or gel tube, 3-5 mL
- Blood culture: Culture bottle, 8-10 mL per bottle, two bottles from different sites
- Coagulation: Citrate tube (blue cap), 2.7 mL, must be filled to the mark
- Blood sugar: Fluoride tube (grey cap), 2 mL
- ABG: Heparinized syringe, must be sent on ice within 15 minutes
- Urine: Clean catch midstream, sterile container for culture
- CSF: 3 tubes — biochemistry, microbiology, cytology

CASE DETAILS:
- Patient: {age}y {gender}
- Chief complaint: {chief_complaint}
- Investigations ordered: {investigations_ordered}
- Results available: {results_available}
- Pending investigations: {pending_investigations}

Respond ONLY as the lab technician. Be professional, factual, and flag critical values."""


class LabTechAgent(BaseAgent):
    """Lab technician agent that processes investigations with realistic delays."""

    agent_type = "lab_tech"
    display_name = "Lab Tech Ramesh"

    def __init__(self):
        super().__init__()
        self.case_info: dict = {}
        self.investigations_ordered: list[str] = []
        self.results_available: dict = {}
        self.pending_investigations: list[str] = []
        self.critical_values: list[str] = []

    def configure(self, case_data: dict):
        """Configure lab tech with case-specific data."""
        self.case_info = {
            "age": case_data.get("patient", {}).get("age", 45),
            "gender": case_data.get("patient", {}).get("gender", "Male"),
            "chief_complaint": case_data.get("chief_complaint", ""),
        }

        # Extract lab/investigation info from stages
        lab_info = ""
        for stage in case_data.get("stages", []):
            stage_name = stage.get("stage", "")
            if stage_name in ("labs", "investigations", "lab_results"):
                lab_info = stage.get("info", "")
                break

        self.case_info["lab_info"] = lab_info

        # Parse available results from lab info
        if lab_info:
            self.results_available = {"lab_results": lab_info}
        else:
            self.results_available = {}

        # Extract investigation list if available
        investigations = case_data.get("investigations", [])
        if isinstance(investigations, list):
            self.investigations_ordered = investigations
        elif isinstance(investigations, str):
            self.investigations_ordered = [
                inv.strip() for inv in investigations.split(",") if inv.strip()
            ]
        else:
            self.investigations_ordered = []

        self.pending_investigations = []

        # Detect critical values in lab info
        self._detect_critical_values(lab_info)

    def _detect_critical_values(self, lab_info: str):
        """Scan lab info for panic/critical values."""
        self.critical_values = []
        if not lab_info:
            return

        lab_lower = lab_info.lower()

        # Check for critical patterns
        critical_checks = [
            ("hb", "hemoglobin", lambda v: v < 7 or v > 20),
            ("platelet", "platelets", lambda v: v < 20000),
            ("wbc", "white blood cell", lambda v: v < 2000 or v > 30000),
            ("glucose", "blood sugar", lambda v: v < 50 or v > 500),
            ("potassium", "k+", lambda v: v < 2.5 or v > 6.5),
            ("sodium", "na+", lambda v: v < 120 or v > 160),
            ("creatinine", "creat", lambda v: v > 10),
            ("inr", "inr", lambda v: v > 5.0),
        ]

        # Simple heuristic: flag keywords that suggest critical values
        if any(word in lab_lower for word in ["critical", "panic", "dangerously", "severely"]):
            self.critical_values.append("Flagged values detected in report")

        # Check for very low platelet counts (common critical value in Indian hospitals)
        import re

        platelet_match = re.search(r"platelet[s]?\s*[:\-]?\s*([\d,]+)", lab_lower)
        if platelet_match:
            try:
                count = int(platelet_match.group(1).replace(",", ""))
                if count < 20000:
                    self.critical_values.append(
                        f"CRITICAL: Platelet count {count:,} — below panic value"
                    )
            except ValueError:
                pass

        hb_match = re.search(r"(?:hb|hemoglobin|haemoglobin)\s*[:\-]?\s*([\d.]+)", lab_lower)
        if hb_match:
            try:
                hb = float(hb_match.group(1))
                if hb < 7:
                    self.critical_values.append(
                        f"CRITICAL: Hemoglobin {hb} g/dL — below panic value"
                    )
            except ValueError:
                pass

    def get_system_prompt(self, case_context: dict) -> str:
        info = {**self.case_info, **case_context}

        investigations_str = ", ".join(self.investigations_ordered) if self.investigations_ordered else "As per doctor's orders"
        results_str = self.case_info.get("lab_info", "Pending") or "Pending"
        pending_str = ", ".join(self.pending_investigations) if self.pending_investigations else "None currently"

        base_prompt = LAB_TECH_SYSTEM_PROMPT.format(
            age=info.get("age", 45),
            gender=info.get("gender", "Male"),
            chief_complaint=info.get("chief_complaint", "unknown"),
            investigations_ordered=investigations_str,
            results_available=results_str,
            pending_investigations=pending_str,
        )

        if self.critical_values:
            base_prompt += (
                "\n\n=== CRITICAL VALUES TO FLAG ===\n"
                "You MUST immediately inform the doctor about these critical values:\n"
                + "\n".join(f"- {cv}" for cv in self.critical_values)
            )

        if self.specialized_knowledge:
            base_prompt += (
                "\n\n=== YOUR LAB EXPERTISE & CASE-SPECIFIC KNOWLEDGE ===\n"
                "Use this specialized knowledge for accurate lab reporting, "
                "turnaround times, and investigation-specific details for this case.\n\n"
                f"{self.specialized_knowledge}"
            )

        return base_prompt

    def get_fallback_response(self, message: str, case_context: dict) -> str:
        msg = message.lower()

        # Critical value alert takes priority
        if self.critical_values:
            for cv in self.critical_values:
                if "platelet" in cv.lower() or "hemoglobin" in cv.lower():
                    return (
                        f"Doctor, urgent update! {cv}. "
                        "I'm flagging this as a panic value per our lab protocol. "
                        "Please review immediately and advise if repeat sample is needed."
                    )

        # Sample collection
        if any(w in msg for w in ["collect", "sample", "draw", "blood"]):
            return (
                "Sir, sample collected. EDTA and plain tubes filled. "
                "Sending to the lab now. Routine turnaround is about 1-2 hours, "
                "I'll try to expedite given the clinical urgency."
            )

        # Report status / ETA
        if any(w in msg for w in ["report", "result", "ready", "status", "kab", "eta"]):
            lab_info = self.case_info.get("lab_info", "")
            if lab_info:
                return (
                    "Doctor, reports are ready. I'm sending them to the ward now. "
                    "Please check — there are a few values I'd like you to review."
                )
            return (
                "Sir, samples are being processed. CBC should be ready in about 45 minutes, "
                "biochemistry in about 1-2 hours. I'll call the ward as soon as reports are ready."
            )

        # CBC related
        if any(w in msg for w in ["cbc", "hemogram", "blood count"]):
            return (
                "Sir, for CBC I need 2 mL in the EDTA tube — purple cap. "
                "Our 5-part analyzer is working, turnaround is about 45 minutes. "
                "I'll flag any critical values immediately."
            )

        # Blood culture
        if any(w in msg for w in ["culture", "blood culture", "sensitivity"]):
            return (
                "Sir, for blood culture we need two samples from different sites, "
                "8-10 mL each in the culture bottles. Please collect before starting antibiotics. "
                "Preliminary report in 24-48 hours, final with sensitivity in 5-7 days."
            )

        # ABG
        if any(w in msg for w in ["abg", "arterial", "blood gas"]):
            return (
                "Sir, ABG sample needs to come in a heparinized syringe, on ice, "
                "within 15 minutes of collection. Our ABG machine is in the ICU. "
                "I can process it in 15-20 minutes if sent immediately."
            )

        # Coagulation
        if any(w in msg for w in ["pt", "inr", "aptt", "coagulation", "clotting"]):
            return (
                "Sir, coagulation profile needs citrate tube — blue cap, 2.7 mL. "
                "Please ensure the tube is filled exactly to the mark, "
                "otherwise we'll have to reject and recollect. Turnaround is about 1-2 hours."
            )

        # Machine / equipment issues
        if any(w in msg for w in ["machine", "down", "delay", "problem", "issue"]):
            return (
                "Sir, I should let you know — our biochemistry analyzer was down for "
                "calibration this morning. It's back up now but there's a backlog. "
                "May take an extra 30-45 minutes for LFT and RFT reports. Sorry for the delay."
            )

        # Urgent / stat
        if any(w in msg for w in ["urgent", "stat", "emergency", "jaldi", "fast"]):
            return (
                "Understood sir, marking this as URGENT. I'll prioritize these samples. "
                "CBC can be ready in 20-30 minutes, sugar in 15 minutes if you need stat. "
                "I'll call the ward directly with results."
            )

        # Urine
        if any(w in msg for w in ["urine", "urine culture", "urinalysis"]):
            return (
                "Sir, for urine routine I need a clean catch midstream sample in a plain container. "
                "If you need culture also, please use the sterile container. "
                "Routine report in 30-45 minutes, culture in 24-48 hours."
            )

        # Cross-match / blood bank
        if any(w in msg for w in ["cross", "crossmatch", "blood bank", "transfusion", "prbc"]):
            return (
                "Sir, for crossmatch I'll need a fresh sample — 3 mL in plain tube with patient's details. "
                "Blood bank takes minimum 30-45 minutes for crossmatch. "
                "What blood group is the patient? I'll check availability."
            )

        # Dengue / malaria (common in Indian hospitals)
        if any(w in msg for w in ["dengue", "malaria", "ns1", "widal", "typhoid"]):
            return (
                "Sir, we have rapid test kits for dengue NS1 and malaria. "
                "Results in about 30 minutes. For dengue serology (IgM/IgG ELISA), "
                "that runs in batch — turnaround is 4-6 hours. What do you want me to run?"
            )

        # Radiology (often asked to lab tech who redirects)
        if any(w in msg for w in ["x-ray", "xray", "ultrasound", "ct", "mri", "scan"]):
            return (
                "Sir, imaging is not my department — you'll need to send a request to Radiology. "
                "X-ray is usually available, turnaround 30 min to 1 hour depending on queue. "
                "For ultrasound, the radiologist needs to be called. CT/MRI needs HOD approval."
            )

        # Default professional response
        return (
            "Yes sir, lab is ready. What investigations do you want me to process? "
            "Just let me know the tests and I'll arrange the appropriate tubes and get samples collected."
        )

    def get_initial_report(self) -> dict:
        """Generate lab tech's introduction when investigation is first ordered."""
        age = self.case_info.get("age", 45)
        gender = self.case_info.get("gender", "Male").lower()
        investigations = self.investigations_ordered

        if investigations:
            inv_list = ", ".join(investigations[:4])
            extra = f" and {len(investigations) - 4} more" if len(investigations) > 4 else ""
            content = (
                f"Good day doctor. I'm Ramesh from the pathology lab. "
                f"I've received the investigation request for your {age}y {gender} patient. "
                f"Orders noted: {inv_list}{extra}. "
                f"I'll collect the samples and start processing. Will update you as reports come in."
            )
        else:
            content = (
                f"Good day doctor. I'm Ramesh from the pathology lab. "
                f"I understand you have a {age}y {gender} patient who needs investigations. "
                f"Let me know what tests you'd like to order and I'll arrange sample collection."
            )

        # Add critical value alert if detected
        if self.critical_values:
            content += (
                f"\n\nURGENT: Doctor, I need to flag something — "
                + "; ".join(self.critical_values)
                + ". Please review immediately."
            )

        return {
            "agent_type": self.agent_type,
            "display_name": self.display_name,
            "content": content,
            "investigations_ordered": self.investigations_ordered,
            "critical_values": self.critical_values,
        }
