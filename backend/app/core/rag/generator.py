import json
import uuid
from typing import Optional

# Sample cases for demo (in production, these would be generated via Claude API + RAG)
SAMPLE_CASES = {
    "cardiology": [
        {
            "patient": {"age": 28, "gender": "Male", "location": "Mumbai"},
            "chief_complaint": "Acute onset chest pain radiating to left arm",
            "initial_presentation": "A 28-year-old male software engineer presents to the ED at 2 AM with crushing chest pain that started 45 minutes ago while sleeping. He appears anxious, diaphoretic, and is clutching his chest. He denies previous cardiac history but mentions significant work stress and recent cocaine use at a party.",
            "vital_signs": {"bp": "160/95", "hr": 110, "rr": 22, "temp": 37.2, "spo2": 96},
            "stages": [
                {"stage": "history", "info": "Pain started suddenly, woke him from sleep. Severity: 8/10, crushing quality. Radiates to left arm and jaw. Associated with nausea and sweating. He admits to cocaine use ~3 hours ago. No prior cardiac history. Family history: father had MI at age 52. Smokes 5 cigarettes/day."},
                {"stage": "physical_exam", "info": "Alert, anxious, diaphoretic. Cardiovascular: Tachycardic, regular rhythm, no murmurs. S1/S2 normal. JVP not elevated. Chest: Clear bilateral air entry. Abdomen: Soft, non-tender. Extremities: No edema. Pupils dilated bilaterally."},
                {"stage": "labs", "info": "ECG: Sinus tachycardia, ST elevation in leads II, III, aVF (inferior leads). Troponin I: 0.8 ng/mL (elevated, normal <0.04). CBC: Normal. BMP: Normal. Urine drug screen: Positive for cocaine. CXR: Normal cardiac silhouette."},
            ],
            "diagnosis": "Cocaine-induced acute coronary syndrome (inferior STEMI)",
            "differentials": ["Acute coronary syndrome (STEMI)", "Cocaine-induced coronary vasospasm", "Aortic dissection", "Pulmonary embolism", "Pericarditis"],
            "learning_points": ["Always screen for substance use in young patients with ACS", "Cocaine causes coronary vasospasm AND increases myocardial oxygen demand", "Beta-blockers are contraindicated in cocaine-induced ACS", "First-line: Benzodiazepines + Nitroglycerin"],
            "atypical_features": "Young age, cocaine use as precipitant, inferior STEMI pattern",
            "specialty": "cardiology",
            "difficulty": "intermediate",
        }
    ],
    "infectious": [
        {
            "patient": {"age": 35, "gender": "Female", "location": "Kochi, Kerala"},
            "chief_complaint": "High-grade fever for 5 days with body aches",
            "initial_presentation": "A 35-year-old housewife presents during monsoon season with 5 days of high-grade fever (103-104\u00b0F), severe myalgia, retro-orbital pain, and a macular rash on her trunk. She lives near a construction site with stagnant water. Her neighbor was recently hospitalized for dengue.",
            "vital_signs": {"bp": "100/70", "hr": 96, "rr": 18, "temp": 39.4, "spo2": 98},
            "stages": [
                {"stage": "history", "info": "Fever started 5 days ago, initially intermittent, now continuous. Severe headache, especially behind the eyes. Diffuse body aches. Noticed rash on trunk 2 days ago. Mild nausea, reduced appetite. No bleeding from any site. LMP: 2 weeks ago, regular. Lives near construction site with stagnant water pools."},
                {"stage": "physical_exam", "info": "Febrile, flushed. Macular blanching rash on trunk. Positive tourniquet test. No petechiae. Mild hepatomegaly (2 cm below costal margin). No splenomegaly. No lymphadenopathy. No signs of plasma leakage. Alert and oriented."},
                {"stage": "labs", "info": "CBC: WBC 3,200 (low), Platelets 45,000 (critically low), Hct 42%. NS1 Antigen: Positive. Dengue IgM: Positive. LFT: AST 180, ALT 120 (elevated). PT/INR: Normal. CRP: Elevated. Blood smear: No malarial parasites."},
            ],
            "diagnosis": "Dengue fever with warning signs (approaching critical phase)",
            "differentials": ["Dengue fever", "Chikungunya", "Malaria", "Typhoid fever", "Leptospirosis"],
            "learning_points": ["Warning signs: Abdominal pain, persistent vomiting, fluid accumulation, mucosal bleeding, lethargy, hepatomegaly >2cm, increasing hematocrit with decreasing platelets", "Critical phase occurs around day 3-7 of illness (defervescence)", "Fluid management is the cornerstone - avoid excessive fluids", "No role for prophylactic platelet transfusion if no active bleeding", "Monitor hematocrit every 6-12 hours during critical phase"],
            "atypical_features": "Classic presentation but requires careful monitoring for transition to severe dengue",
            "specialty": "infectious",
            "difficulty": "beginner",
        }
    ],
    "neurology": [
        {
            "patient": {"age": 42, "gender": "Male", "location": "Delhi"},
            "chief_complaint": "Progressive weakness in legs for 3 days",
            "initial_presentation": "A 42-year-old schoolteacher presents with progressive ascending weakness starting in both feet 3 days ago, now reaching his thighs. He had a viral upper respiratory infection 2 weeks ago. He reports tingling in his fingers since this morning and is having difficulty climbing stairs.",
            "vital_signs": {"bp": "130/80", "hr": 88, "rr": 20, "temp": 37.0, "spo2": 97},
            "stages": [
                {"stage": "history", "info": "Weakness started in feet, ascending to thighs over 3 days. Symmetric involvement. Tingling/numbness in fingertips since morning. Had a 'cold' 2 weeks ago with sore throat and runny nose. Back pain between shoulder blades. No bowel/bladder dysfunction yet. No recent vaccinations. No travel history."},
                {"stage": "physical_exam", "info": "Power: Lower limbs 3/5 proximally, 2/5 distally. Upper limbs 4/5. Deep tendon reflexes: Absent in lower limbs, reduced in upper limbs. Plantars: Mute bilaterally. Sensation: Glove-and-stocking pattern of reduced light touch. Cranial nerves: Intact. Respiratory: Using accessory muscles slightly. FVC: 1.8L (predicted 3.5L) - CRITICAL."},
                {"stage": "labs", "info": "NCS/EMG: Demyelinating pattern with prolonged distal latencies, reduced conduction velocities, conduction blocks. CSF: Protein 1.2 g/L (elevated), WBC 3 cells (albuminocytological dissociation). MRI spine: Enhancement of cauda equina nerve roots. ABG: pH 7.38, pCO2 44 (borderline). Spirometry: FVC declining - was 2.2L yesterday."},
            ],
            "diagnosis": "Guillain-Barr\u00e9 Syndrome (acute inflammatory demyelinating polyneuropathy) with impending respiratory failure",
            "differentials": ["Guillain-Barr\u00e9 Syndrome", "Transverse myelitis", "Myasthenia gravis", "Hypokalemic periodic paralysis", "Acute poliomyelitis"],
            "learning_points": ["FVC < 20 mL/kg or declining FVC is an indication for ICU admission and potential intubation", "Albuminocytological dissociation (high protein, normal cells) in CSF is characteristic", "Treatment: IVIg or plasmapheresis - both equally effective", "20-30% of GBS patients require mechanical ventilation", "Autonomic dysfunction (BP fluctuations, arrhythmias) is a major cause of mortality"],
            "atypical_features": "Rapidly progressive with early respiratory compromise - requires urgent intervention",
            "specialty": "neurology",
            "difficulty": "advanced",
        }
    ],
}


class CaseGenerator:
    def __init__(self):
        self.active_cases: dict = {}

    def generate_case(self, specialty: str, difficulty: str = "intermediate", year_level: str = "final_year") -> dict:
        case_id = str(uuid.uuid4())[:8]

        # Get sample case for the specialty
        specialty_cases = SAMPLE_CASES.get(specialty, SAMPLE_CASES.get("cardiology", []))
        if not specialty_cases:
            specialty_cases = list(SAMPLE_CASES.values())[0]

        case_data = specialty_cases[0].copy()
        case_data["id"] = case_id

        self.active_cases[case_id] = case_data
        return case_data

    def get_case(self, case_id: str) -> Optional[dict]:
        return self.active_cases.get(case_id)

    def process_action(self, case_id: str, action_type: str, student_input: Optional[str] = None) -> dict:
        case = self.active_cases.get(case_id)
        if not case:
            return {"error": "Case not found"}

        stage_map = {
            "take_history": 0,
            "physical_exam": 1,
            "order_labs": 2,
        }

        stage_index = stage_map.get(action_type)
        if stage_index is not None and stage_index < len(case.get("stages", [])):
            return {
                "action": action_type,
                "result": case["stages"][stage_index],
            }

        return {"action": action_type, "result": "Action processed"}

    def evaluate_diagnosis(self, case_id: str, diagnosis: str, reasoning: str = "") -> dict:
        case = self.active_cases.get(case_id)
        if not case:
            return {"error": "Case not found"}

        correct_diagnosis = case.get("diagnosis", "").lower()
        student_diagnosis = diagnosis.lower()

        # Simple matching
        is_correct = any(
            keyword in student_diagnosis
            for keyword in correct_diagnosis.split()
            if len(keyword) > 3
        )

        return {
            "student_diagnosis": diagnosis,
            "correct_diagnosis": case["diagnosis"],
            "is_correct": is_correct,
            "differentials": case.get("differentials", []),
            "learning_points": case.get("learning_points", []),
            "feedback": "Excellent clinical reasoning!" if is_correct else f"The correct diagnosis is {case['diagnosis']}. Review the key learning points.",
        }
