"""Complication Engine — probabilistic complications, time-based triggers, urgent interruptions.

This engine makes clinical simulations DANGEROUS and UNPREDICTABLE — just like real
medicine. Complications don't happen randomly; they emerge from untreated conditions,
delayed interventions, and the natural disease trajectory. Every complication is
clinically realistic, specialty-appropriate, and time-dependent.

Works alongside CaseStateManager: the state manager tracks vitals/investigations/time,
the complication engine decides WHAT GOES WRONG and WHEN.

Architecture:
    Orchestrator
        -> advance_time() on CaseStateManager
        -> check_complications() on ComplicationEngine
        -> Merge events, deliver to student via agents

Each tick of the simulation clock, the engine:
    1. Evaluates every possible complication for this case
    2. Calculates time-dependent probability (rises if untreated)
    3. Checks vitals criteria (some complications only fire when vitals are deranged)
    4. Checks if preventive treatment was given
    5. Rolls the dice — if triggered, generates a SimulationEvent
    6. Escalates trajectory on the state manager when appropriate
"""

import logging
import random
import uuid
from typing import Optional

from .case_state_manager import (
    CaseStateManager,
    PatientTrajectory,
    SimulationEvent,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Specialty complication registry
# ---------------------------------------------------------------------------
# Each complication is a dict with:
#   name             — clinical name
#   description      — what happens clinically
#   probability_base — base probability per check (0.0-1.0) before modifiers
#   time_window      — (min_minutes, max_minutes) when this can fire
#   vitals_criteria  — dict of vital sign thresholds that INCREASE probability
#   treatment_prevents — list of treatment keywords that would prevent this
#   urgency          — "urgent" or "critical"
#   agent_message    — what the nurse/patient says when it triggers
#   trajectory_effect — what happens to patient trajectory when this fires
# ---------------------------------------------------------------------------

SPECIALTY_COMPLICATIONS: dict[str, list[dict]] = {
    "cardiology": [
        {
            "name": "Cardiogenic Shock",
            "description": "Pump failure with hypotension and end-organ hypoperfusion following acute MI",
            "probability_base": 0.15,
            "time_window": (30, 180),
            "vitals_criteria": {"bp_systolic_below": 90, "hr_above": 110},
            "treatment_prevents": ["pci", "thrombolysis", "streptokinase", "tenecteplase", "aspirin", "heparin", "inotrope", "dobutamine"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient is cold, clammy, and confused. BP has crashed to {bp_systolic}/{bp_diastolic}. Urine output has dropped. I think we're losing him!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Ventricular Tachycardia",
            "description": "Sustained VT from ischemic myocardium — can degenerate to VF",
            "probability_base": 0.12,
            "time_window": (15, 120),
            "vitals_criteria": {"hr_above": 120},
            "treatment_prevents": ["amiodarone", "lidocaine", "beta_blocker", "metoprolol", "defibrillation", "cardioversion"],
            "urgency": "critical",
            "agent_message": "Doctor! Monitor is showing wide-complex tachycardia! HR is {hr}! Patient says chest feels like it's going to explode!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Acute Heart Failure / Pulmonary Edema",
            "description": "Fluid backs up into lungs from failing left ventricle",
            "probability_base": 0.10,
            "time_window": (30, 240),
            "vitals_criteria": {"spo2_below": 92, "rr_above": 24},
            "treatment_prevents": ["furosemide", "lasix", "nitroglycerin", "ntg", "oxygen", "niv", "bipap", "cpap"],
            "urgency": "urgent",
            "agent_message": "Doctor, patient is sitting bolt upright gasping for air. Pink frothy sputum! SpO2 is {spo2}% on room air. I can hear crackles from the doorway!",
            "trajectory_effect": "deteriorating",
        },
        {
            "name": "Cardiac Arrest — VF/Pulseless VT",
            "description": "Cardiac arrest from lethal arrhythmia in acute coronary syndrome",
            "probability_base": 0.05,
            "time_window": (60, 300),
            "vitals_criteria": {"bp_systolic_below": 70, "hr_above": 150},
            "treatment_prevents": ["pci", "thrombolysis", "amiodarone", "defibrillation"],
            "urgency": "critical",
            "agent_message": "CODE BLUE! Patient is unresponsive, no pulse! Monitor shows VF! Starting CPR — we need you here NOW!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Pericardial Tamponade",
            "description": "Fluid accumulation in pericardial sac compressing the heart",
            "probability_base": 0.05,
            "time_window": (45, 240),
            "vitals_criteria": {"bp_systolic_below": 90, "hr_above": 100},
            "treatment_prevents": ["pericardiocentesis", "echo", "echocardiography"],
            "urgency": "critical",
            "agent_message": "Doctor, Beck's triad! Muffled heart sounds, JVP is sky high, and BP keeps dropping. I think there's fluid around the heart!",
            "trajectory_effect": "critical",
        },
    ],

    "respiratory": [
        {
            "name": "Respiratory Failure — Type 1",
            "description": "Hypoxemic respiratory failure requiring mechanical ventilation",
            "probability_base": 0.15,
            "time_window": (30, 180),
            "vitals_criteria": {"spo2_below": 88, "rr_above": 30},
            "treatment_prevents": ["oxygen", "niv", "bipap", "cpap", "intubation", "ventilator", "high_flow_nasal_cannula"],
            "urgency": "critical",
            "agent_message": "Doctor! SpO2 is {spo2}% despite oxygen! Patient is using accessory muscles, can barely speak. RR is {rr}. Do we intubate?",
            "trajectory_effect": "critical",
        },
        {
            "name": "Tension Pneumothorax",
            "description": "Air trapped in pleural space causing mediastinal shift and cardiovascular collapse",
            "probability_base": 0.08,
            "time_window": (15, 120),
            "vitals_criteria": {"bp_systolic_below": 90, "spo2_below": 88},
            "treatment_prevents": ["needle_decompression", "chest_tube", "icd", "intercostal_drain"],
            "urgency": "critical",
            "agent_message": "Doctor! Absent breath sounds on one side, trachea is shifted! BP is dropping fast — {bp_systolic}/{bp_diastolic}! I think it's a tension pneumothorax!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Massive Hemoptysis",
            "description": "Large-volume blood in airways threatening asphyxiation",
            "probability_base": 0.06,
            "time_window": (20, 180),
            "vitals_criteria": {"hr_above": 110, "spo2_below": 92},
            "treatment_prevents": ["tranexamic_acid", "blood_transfusion", "interventional_radiology", "bronchoscopy"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient is coughing up large amounts of bright red blood! There's blood everywhere — I estimate over 200ml already! SpO2 falling!",
            "trajectory_effect": "critical",
        },
        {
            "name": "ARDS Development",
            "description": "Acute respiratory distress syndrome with bilateral infiltrates and refractory hypoxemia",
            "probability_base": 0.10,
            "time_window": (60, 360),
            "vitals_criteria": {"spo2_below": 90, "rr_above": 28},
            "treatment_prevents": ["lung_protective_ventilation", "prone_positioning", "niv", "intubation", "steroids"],
            "urgency": "urgent",
            "agent_message": "Doctor, despite high-flow oxygen, SpO2 won't come above {spo2}%. Bilateral infiltrates on chest X-ray. P/F ratio is very low. This looks like ARDS.",
            "trajectory_effect": "deteriorating",
        },
    ],

    "infectious": [
        {
            "name": "Septic Shock",
            "description": "Distributive shock from overwhelming infection with vasodilation and organ hypoperfusion",
            "probability_base": 0.18,
            "time_window": (30, 120),
            "vitals_criteria": {"bp_systolic_below": 90, "hr_above": 110, "temp_above": 38.5},
            "treatment_prevents": ["antibiotics", "iv_fluids", "noradrenaline", "vasopressor", "normal_saline", "ringer_lactate"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient is burning up at {temp}C but extremities are cold! BP is {bp_systolic}/{bp_diastolic} — not responding to fluids. Altered sensorium. I think we're heading into septic shock!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Disseminated Intravascular Coagulation",
            "description": "DIC with simultaneous clotting and bleeding from consumptive coagulopathy",
            "probability_base": 0.08,
            "time_window": (60, 240),
            "vitals_criteria": {"hr_above": 120, "bp_systolic_below": 90},
            "treatment_prevents": ["antibiotics", "source_control", "ffp", "cryoprecipitate", "platelet_transfusion"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient is oozing from IV sites and gums. Petechiae all over. I can see blood in the urine bag. Labs show very low platelets and high INR!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Multi-Organ Dysfunction",
            "description": "Progressive failure of multiple organ systems from uncontrolled sepsis",
            "probability_base": 0.10,
            "time_window": (90, 360),
            "vitals_criteria": {"bp_systolic_below": 80, "spo2_below": 90},
            "treatment_prevents": ["antibiotics", "iv_fluids", "vasopressor", "organ_support", "icu_transfer"],
            "urgency": "critical",
            "agent_message": "Doctor, patient is oliguric, creatinine is rising, bilirubin is up, and now SpO2 is {spo2}%. Multiple organs are failing. We need ICU!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Severe Drug Reaction — Anaphylaxis",
            "description": "Anaphylactic reaction to administered antibiotic",
            "probability_base": 0.04,
            "time_window": (5, 60),
            "vitals_criteria": {"bp_systolic_below": 90},
            "treatment_prevents": ["test_dose", "allergy_check", "adrenaline", "epinephrine", "hydrocortisone", "chlorpheniramine"],
            "urgency": "critical",
            "agent_message": "Doctor! After the antibiotic injection, patient has developed rash, lip swelling, and is wheezing! BP dropping to {bp_systolic}/{bp_diastolic}! Looks like anaphylaxis!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Dengue Hemorrhagic Manifestations",
            "description": "Plasma leakage and hemorrhagic manifestations in severe dengue",
            "probability_base": 0.20,
            "time_window": (60, 240),
            "vitals_criteria": {"bp_systolic_below": 100, "hr_above": 100},
            "treatment_prevents": ["iv_fluids", "platelet_transfusion", "monitoring", "close_observation"],
            "urgency": "urgent",
            "agent_message": "Doctor, patient has petechiae and gum bleeding. Hematocrit is rising — plasma leakage! Platelet count is dropping fast. BP narrowing — pulse pressure is only 20mmHg!",
            "trajectory_effect": "deteriorating",
        },
    ],

    "neurology": [
        {
            "name": "Cerebral Herniation",
            "description": "Brainstem compression from raised intracranial pressure — uncal or tonsillar herniation",
            "probability_base": 0.12,
            "time_window": (30, 180),
            "vitals_criteria": {"bp_systolic_above": 180, "hr_below": 60},
            "treatment_prevents": ["mannitol", "hypertonic_saline", "decompressive_craniectomy", "neurosurgery_consult", "head_elevation"],
            "urgency": "critical",
            "agent_message": "Doctor! One pupil is fixed and dilated! Patient has Cushing's triad — hypertension, bradycardia, irregular breathing. GCS is dropping! I think the brain is herniating!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Status Epilepticus",
            "description": "Continuous seizure activity lasting >5 minutes or recurrent seizures without regaining consciousness",
            "probability_base": 0.10,
            "time_window": (15, 120),
            "vitals_criteria": {"hr_above": 120, "temp_above": 38.0},
            "treatment_prevents": ["lorazepam", "diazepam", "midazolam", "phenytoin", "levetiracetam", "valproate", "anticonvulsant"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient is seizing — tonic-clonic movements, frothing at the mouth! It's been going on for 5 minutes! We need to stop this NOW!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Raised ICP — Deterioration",
            "description": "Progressive rise in intracranial pressure with decreasing consciousness",
            "probability_base": 0.12,
            "time_window": (30, 240),
            "vitals_criteria": {"bp_systolic_above": 160},
            "treatment_prevents": ["mannitol", "hypertonic_saline", "head_elevation", "ct_scan", "neurosurgery_consult"],
            "urgency": "urgent",
            "agent_message": "Doctor, patient's GCS has dropped from 12 to 9. Projectile vomiting. Headache is excruciating. BP is {bp_systolic}/{bp_diastolic} — I think ICP is rising!",
            "trajectory_effect": "deteriorating",
        },
        {
            "name": "Autonomic Storm",
            "description": "Paroxysmal sympathetic hyperactivity with tachycardia, hypertension, diaphoresis, and posturing",
            "probability_base": 0.06,
            "time_window": (60, 300),
            "vitals_criteria": {"hr_above": 130, "temp_above": 38.5, "bp_systolic_above": 170},
            "treatment_prevents": ["beta_blocker", "propranolol", "morphine", "bromocriptine", "sedation", "midazolam"],
            "urgency": "urgent",
            "agent_message": "Doctor, patient is pouring sweat, HR is {hr}, BP is {bp_systolic}/{bp_diastolic}, posturing! Temperature is {temp}C. This looks like an autonomic storm!",
            "trajectory_effect": "deteriorating",
        },
    ],

    "gastroenterology": [
        {
            "name": "Massive Upper GI Bleed",
            "description": "Torrential hematemesis or melena with hemodynamic instability",
            "probability_base": 0.15,
            "time_window": (15, 180),
            "vitals_criteria": {"hr_above": 110, "bp_systolic_below": 90},
            "treatment_prevents": ["iv_fluids", "blood_transfusion", "ppi", "pantoprazole", "octreotide", "endoscopy", "sengstaken_tube"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient just vomited a large amount of dark blood — nearly 500ml! HR is {hr}, BP dropping to {bp_systolic}/{bp_diastolic}! We need blood urgently!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Hepatic Encephalopathy",
            "description": "Altered consciousness from hepatic failure with asterixis progressing to coma",
            "probability_base": 0.12,
            "time_window": (60, 300),
            "vitals_criteria": {},
            "treatment_prevents": ["lactulose", "rifaximin", "protein_restriction", "enema"],
            "urgency": "urgent",
            "agent_message": "Doctor, patient has become drowsy and confused. Flapping tremor present. I smell fetor hepaticus. I think the liver is failing — hepatic encephalopathy!",
            "trajectory_effect": "deteriorating",
        },
        {
            "name": "Spontaneous Bacterial Peritonitis",
            "description": "Infection of ascitic fluid in a cirrhotic patient",
            "probability_base": 0.10,
            "time_window": (30, 240),
            "vitals_criteria": {"temp_above": 38.0, "hr_above": 100},
            "treatment_prevents": ["antibiotics", "cefotaxime", "diagnostic_paracentesis", "ascitic_fluid_analysis"],
            "urgency": "urgent",
            "agent_message": "Doctor, the patient's abdomen is becoming more tender and distended. Temperature spiking to {temp}C. Abdominal guarding present. Could be SBP!",
            "trajectory_effect": "deteriorating",
        },
        {
            "name": "Variceal Rupture",
            "description": "Esophageal variceal hemorrhage with massive hematemesis in portal hypertension",
            "probability_base": 0.10,
            "time_window": (15, 120),
            "vitals_criteria": {"hr_above": 120, "bp_systolic_below": 85},
            "treatment_prevents": ["octreotide", "terlipressin", "sengstaken_tube", "endoscopy", "band_ligation"],
            "urgency": "critical",
            "agent_message": "Doctor! Torrential hematemesis — bright red blood everywhere! Patient is going into shock — HR {hr}, BP {bp_systolic}/{bp_diastolic}! Known varices — this is a bleed!",
            "trajectory_effect": "critical",
        },
    ],

    "emergency": [
        {
            "name": "Hemorrhagic Shock",
            "description": "Class III/IV hemorrhagic shock from ongoing blood loss",
            "probability_base": 0.15,
            "time_window": (15, 120),
            "vitals_criteria": {"hr_above": 120, "bp_systolic_below": 80},
            "treatment_prevents": ["iv_fluids", "blood_transfusion", "crossmatch", "massive_transfusion", "surgical_consult"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient is tachycardic at {hr}, BP is {bp_systolic}/{bp_diastolic}, cold and clammy! Altered consciousness! This is Class III shock — we need blood NOW!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Anaphylaxis",
            "description": "Severe systemic allergic reaction with airway compromise and cardiovascular collapse",
            "probability_base": 0.05,
            "time_window": (5, 45),
            "vitals_criteria": {"bp_systolic_below": 90, "spo2_below": 92},
            "treatment_prevents": ["adrenaline", "epinephrine", "hydrocortisone", "chlorpheniramine", "nebulization"],
            "urgency": "critical",
            "agent_message": "Doctor! Sudden urticaria, tongue swelling, stridor developing! BP crashing to {bp_systolic}/{bp_diastolic}! ANAPHYLAXIS — need adrenaline STAT!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Rhabdomyolysis — Acute Kidney Injury",
            "description": "Myoglobin release causing acute kidney injury with dark urine and rising creatinine",
            "probability_base": 0.08,
            "time_window": (60, 360),
            "vitals_criteria": {"hr_above": 100},
            "treatment_prevents": ["iv_fluids", "aggressive_hydration", "normal_saline", "alkalinization"],
            "urgency": "urgent",
            "agent_message": "Doctor, patient's urine has turned dark brown — looks like cola. Muscles are very tender. I suspect rhabdomyolysis — we need to push fluids before the kidneys fail!",
            "trajectory_effect": "deteriorating",
        },
        {
            "name": "Compartment Syndrome",
            "description": "Rising intra-compartmental pressure threatening limb viability",
            "probability_base": 0.08,
            "time_window": (30, 240),
            "vitals_criteria": {"hr_above": 100},
            "treatment_prevents": ["fasciotomy", "orthopedic_consult", "surgical_consult", "cast_removal", "elevation"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient screaming with pain out of proportion. Limb is tense and swollen. Pain on passive stretch! Pulses getting weak — compartment syndrome! We need surgery!",
            "trajectory_effect": "deteriorating",
        },
    ],

    "nephrology": [
        {
            "name": "Hyperkalemia — Cardiac Arrest",
            "description": "Lethal arrhythmia from critically elevated serum potassium",
            "probability_base": 0.12,
            "time_window": (30, 180),
            "vitals_criteria": {"hr_below": 50},
            "treatment_prevents": ["calcium_gluconate", "insulin_dextrose", "salbutamol", "kayexalate", "sodium_bicarbonate", "dialysis"],
            "urgency": "critical",
            "agent_message": "Doctor! ECG showing tall peaked T waves and widening QRS! HR is dropping — {hr}! Potassium must be dangerously high. Patient is getting bradycardic!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Flash Pulmonary Edema",
            "description": "Acute pulmonary edema from fluid overload in oliguric renal failure",
            "probability_base": 0.12,
            "time_window": (30, 240),
            "vitals_criteria": {"spo2_below": 90, "rr_above": 28},
            "treatment_prevents": ["furosemide", "dialysis", "fluid_restriction", "niv", "bipap", "oxygen"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient can't breathe — sitting upright, pink frothy sputum! SpO2 is {spo2}%! Fluid overload — the kidneys aren't making urine. We need urgent dialysis or diuretics!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Uremic Encephalopathy",
            "description": "Altered consciousness from accumulation of uremic toxins",
            "probability_base": 0.08,
            "time_window": (60, 360),
            "vitals_criteria": {},
            "treatment_prevents": ["dialysis", "hemodialysis"],
            "urgency": "urgent",
            "agent_message": "Doctor, patient is confused, drowsy, and has asterixis. Breath smells uremic. Creatinine must be very high. I think the toxins are affecting the brain!",
            "trajectory_effect": "deteriorating",
        },
    ],

    "endocrinology": [
        {
            "name": "Thyroid Storm",
            "description": "Life-threatening thyrotoxicosis with hyperpyrexia, tachycardia, and altered consciousness",
            "probability_base": 0.10,
            "time_window": (30, 180),
            "vitals_criteria": {"hr_above": 140, "temp_above": 39.0},
            "treatment_prevents": ["propranolol", "beta_blocker", "ptu", "methimazole", "lugol_iodine", "hydrocortisone"],
            "urgency": "critical",
            "agent_message": "Doctor! HR is {hr}, temperature is {temp}C and climbing! Patient is agitated, tremulous, and drenched in sweat. Thyroid storm — we need beta-blockers and PTU NOW!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Adrenal Crisis",
            "description": "Acute adrenal insufficiency with refractory hypotension and shock",
            "probability_base": 0.08,
            "time_window": (30, 180),
            "vitals_criteria": {"bp_systolic_below": 80},
            "treatment_prevents": ["hydrocortisone", "steroid", "dexamethasone", "iv_fluids", "fludrocortisone"],
            "urgency": "critical",
            "agent_message": "Doctor! BP is {bp_systolic}/{bp_diastolic} and NOT responding to IV fluids at all! Patient is hyperpigmented and severely hypotensive. Could this be adrenal crisis?",
            "trajectory_effect": "critical",
        },
        {
            "name": "Severe Hypoglycemia — Seizure/Coma",
            "description": "Critical hypoglycemia causing seizures or loss of consciousness",
            "probability_base": 0.10,
            "time_window": (15, 120),
            "vitals_criteria": {"hr_above": 100},
            "treatment_prevents": ["dextrose", "d25", "d50", "glucagon", "glucose", "blood_sugar_check"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient is having a seizure! Cold, sweaty, and unresponsive! Glucometer shows 28 mg/dL — critically low sugar! Give IV dextrose STAT!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Cerebral Edema in DKA",
            "description": "Brain swelling from too-rapid correction of DKA, especially in young patients",
            "probability_base": 0.06,
            "time_window": (120, 480),
            "vitals_criteria": {"bp_systolic_above": 140},
            "treatment_prevents": ["gradual_correction", "slow_insulin", "monitoring", "mannitol", "hypertonic_saline"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient was improving but now suddenly has severe headache, vomiting, and decreasing consciousness! Pupils are sluggish. I think it's cerebral edema from DKA correction!",
            "trajectory_effect": "critical",
        },
    ],

    "pediatrics": [
        {
            "name": "Febrile Seizure — Complex",
            "description": "Prolonged or focal seizure triggered by high fever in a child",
            "probability_base": 0.12,
            "time_window": (10, 90),
            "vitals_criteria": {"temp_above": 39.0, "hr_above": 140},
            "treatment_prevents": ["paracetamol", "ibuprofen", "tepid_sponging", "diazepam", "midazolam", "antipyretic"],
            "urgency": "critical",
            "agent_message": "Doctor! The child is seizing — whole body shaking, eyes rolled up! Mother is panicking! Temperature was {temp}C. It's been going on for 3 minutes!",
            "trajectory_effect": "deteriorating",
        },
        {
            "name": "Dehydration Shock",
            "description": "Severe dehydration progressing to hypovolemic shock in a child",
            "probability_base": 0.15,
            "time_window": (30, 180),
            "vitals_criteria": {"hr_above": 150, "bp_systolic_below": 70},
            "treatment_prevents": ["iv_fluids", "ors", "normal_saline", "ringer_lactate", "bolus"],
            "urgency": "critical",
            "agent_message": "Doctor! Child is lethargic with sunken eyes, dry mouth, and no tears! Skin turgor very poor. CRT >4 seconds. HR is {hr}. This child is in shock!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Reye Syndrome",
            "description": "Hepatic failure and encephalopathy following viral illness, especially with aspirin use",
            "probability_base": 0.03,
            "time_window": (60, 360),
            "vitals_criteria": {},
            "treatment_prevents": ["avoid_aspirin", "supportive_care", "mannitol", "icu_transfer"],
            "urgency": "critical",
            "agent_message": "Doctor! Child was recovering but now has persistent vomiting and is becoming confused. Liver is enlarged and tender. Was aspirin given? I'm worried about Reye syndrome!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Kernicterus Progression",
            "description": "Bilirubin encephalopathy with opisthotonus and neurological damage in neonate",
            "probability_base": 0.06,
            "time_window": (120, 480),
            "vitals_criteria": {},
            "treatment_prevents": ["phototherapy", "exchange_transfusion", "bilirubin_monitoring"],
            "urgency": "critical",
            "agent_message": "Doctor! The baby is arching backward — opisthotonus! High-pitched cry, not feeding. The jaundice has deepened. Bilirubin must be dangerously high — kernicterus!",
            "trajectory_effect": "critical",
        },
    ],

    "obstetrics": [
        {
            "name": "Eclampsia",
            "description": "Tonic-clonic seizures in pre-eclampsia with risk of maternal and fetal death",
            "probability_base": 0.12,
            "time_window": (15, 180),
            "vitals_criteria": {"bp_systolic_above": 160},
            "treatment_prevents": ["magnesium_sulphate", "mgso4", "labetalol", "nifedipine", "antihypertensive"],
            "urgency": "critical",
            "agent_message": "Doctor! The patient is seizing — eclampsia! BP was {bp_systolic}/{bp_diastolic}! She needs magnesium sulphate immediately! Fetal heart rate is dipping!",
            "trajectory_effect": "critical",
        },
        {
            "name": "DIC in Obstetrics",
            "description": "Consumptive coagulopathy from placental abruption, amniotic fluid embolism, or HELLP",
            "probability_base": 0.06,
            "time_window": (30, 240),
            "vitals_criteria": {"hr_above": 120, "bp_systolic_below": 90},
            "treatment_prevents": ["blood_transfusion", "ffp", "cryoprecipitate", "platelet_transfusion", "delivery"],
            "urgency": "critical",
            "agent_message": "Doctor! Uncontrollable bleeding from all IV sites! Blood not clotting in the tube! Uterus is not contracting. This is DIC — we need blood products STAT!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Amniotic Fluid Embolism",
            "description": "Catastrophic amniotic fluid entering maternal circulation causing cardiorespiratory collapse",
            "probability_base": 0.03,
            "time_window": (15, 120),
            "vitals_criteria": {"spo2_below": 88, "bp_systolic_below": 80},
            "treatment_prevents": ["supportive_care", "intubation", "vasopressor", "blood_products"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient suddenly collapsed — can't breathe, cyanotic, SpO2 is {spo2}%! Hypotensive at {bp_systolic}/{bp_diastolic}! Amniotic fluid embolism — CODE BLUE!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Uterine Rupture",
            "description": "Catastrophic rupture of the uterine wall during labor",
            "probability_base": 0.04,
            "time_window": (30, 180),
            "vitals_criteria": {"hr_above": 120, "bp_systolic_below": 90},
            "treatment_prevents": ["monitoring", "cesarean_section", "surgical_consult", "oxytocin_stop"],
            "urgency": "critical",
            "agent_message": "Doctor! Sudden severe abdominal pain — patient screaming! Contractions have stopped but there's a bulge in the abdomen. Fetal heart lost! Uterine rupture — we need emergency surgery!",
            "trajectory_effect": "critical",
        },
    ],

    "hematology": [
        {
            "name": "Massive Hemorrhage",
            "description": "Life-threatening bleeding from severe thrombocytopenia or coagulopathy",
            "probability_base": 0.12,
            "time_window": (30, 240),
            "vitals_criteria": {"hr_above": 120, "bp_systolic_below": 85},
            "treatment_prevents": ["platelet_transfusion", "blood_transfusion", "ffp", "tranexamic_acid"],
            "urgency": "critical",
            "agent_message": "Doctor! Massive epistaxis and gum bleeding won't stop! Now blood in urine and stool! BP is {bp_systolic}/{bp_diastolic}, HR {hr}! We need platelets and blood urgently!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Tumor Lysis Syndrome",
            "description": "Metabolic emergency from rapid cell death after chemotherapy with hyperkalemia, hyperphosphatemia, and AKI",
            "probability_base": 0.10,
            "time_window": (60, 360),
            "vitals_criteria": {"hr_above": 100},
            "treatment_prevents": ["rasburicase", "allopurinol", "iv_fluids", "alkalinization", "monitoring"],
            "urgency": "urgent",
            "agent_message": "Doctor, patient is having muscle cramps, palpitations, and reduced urine output after chemotherapy. ECG shows peaked T waves! I think it's tumor lysis syndrome!",
            "trajectory_effect": "deteriorating",
        },
        {
            "name": "Febrile Neutropenia — Sepsis",
            "description": "Overwhelming infection in a neutropenic patient progressing to sepsis",
            "probability_base": 0.15,
            "time_window": (15, 120),
            "vitals_criteria": {"temp_above": 38.3, "hr_above": 100},
            "treatment_prevents": ["antibiotics", "empirical_antibiotics", "blood_culture", "piperacillin_tazobactam", "meropenem"],
            "urgency": "critical",
            "agent_message": "Doctor! Neutropenic patient spiking fever of {temp}C with rigors! HR is {hr}. This is febrile neutropenia — needs broad-spectrum antibiotics within the hour or we'll lose him!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Hyperviscosity Syndrome",
            "description": "Blood hyperviscosity from high paraprotein levels causing neurological and visual symptoms",
            "probability_base": 0.06,
            "time_window": (60, 300),
            "vitals_criteria": {"bp_systolic_above": 160},
            "treatment_prevents": ["plasmapheresis", "plasma_exchange", "hydration"],
            "urgency": "urgent",
            "agent_message": "Doctor, patient complains of blurred vision, headache, and confusion. Fundoscopy shows engorged veins and hemorrhages. Blood is 'thick' — hyperviscosity syndrome!",
            "trajectory_effect": "deteriorating",
        },
    ],

    "psychiatry": [
        {
            "name": "Neuroleptic Malignant Syndrome",
            "description": "Life-threatening reaction to antipsychotics with hyperthermia, rigidity, and autonomic instability",
            "probability_base": 0.06,
            "time_window": (60, 480),
            "vitals_criteria": {"temp_above": 39.5, "hr_above": 120},
            "treatment_prevents": ["stop_antipsychotic", "dantrolene", "bromocriptine", "cooling", "icu_transfer"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient on antipsychotics is rigid as a board! Temperature is {temp}C, HR {hr}, profusely sweating. Lead-pipe rigidity everywhere. NMS — stop the antipsychotic!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Serotonin Syndrome",
            "description": "Serotonin toxicity from drug interaction with agitation, clonus, and hyperthermia",
            "probability_base": 0.06,
            "time_window": (30, 240),
            "vitals_criteria": {"temp_above": 38.5, "hr_above": 110},
            "treatment_prevents": ["stop_serotonergic", "cyproheptadine", "benzodiazepine", "cooling"],
            "urgency": "urgent",
            "agent_message": "Doctor, patient is agitated, tremulous, with clonus at the ankles. Pupils are dilated. Temperature rising to {temp}C. Multiple serotonergic drugs on the chart — serotonin syndrome!",
            "trajectory_effect": "deteriorating",
        },
        {
            "name": "Violent Agitation Episode",
            "description": "Acute behavioral emergency with risk of harm to self or others",
            "probability_base": 0.10,
            "time_window": (10, 120),
            "vitals_criteria": {"hr_above": 110},
            "treatment_prevents": ["haloperidol", "lorazepam", "midazolam", "de_escalation", "restraint"],
            "urgency": "urgent",
            "agent_message": "Doctor! Patient has become violently agitated — throwing things, threatening staff! Two nurses needed to restrain. Screaming that people are trying to kill him. We need sedation NOW!",
            "trajectory_effect": "deteriorating",
        },
    ],

    "dermatology": [
        {
            "name": "SJS Progression to TEN",
            "description": "Stevens-Johnson syndrome progressing to toxic epidermal necrolysis (>30% BSA detachment)",
            "probability_base": 0.10,
            "time_window": (60, 360),
            "vitals_criteria": {"temp_above": 38.5, "hr_above": 100},
            "treatment_prevents": ["stop_offending_drug", "icu_transfer", "cyclosporine", "ivig", "wound_care", "fluid_resuscitation"],
            "urgency": "critical",
            "agent_message": "Doctor! Skin is sloughing off in sheets — Nikolsky sign positive everywhere! Mucosal involvement — eyes, mouth, genitals. This has progressed to TEN — needs burns unit/ICU!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Secondary Sepsis from Skin",
            "description": "Overwhelming infection through denuded skin barrier",
            "probability_base": 0.08,
            "time_window": (60, 360),
            "vitals_criteria": {"temp_above": 38.5, "hr_above": 110, "bp_systolic_below": 90},
            "treatment_prevents": ["antibiotics", "wound_care", "barrier_nursing", "iv_fluids"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient with skin lesions is now spiking to {temp}C with rigors! BP dropping to {bp_systolic}/{bp_diastolic}. Wounds look infected. Sepsis through the skin!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Airway Compromise from Angioedema",
            "description": "Progressive angioedema threatening airway patency",
            "probability_base": 0.06,
            "time_window": (10, 90),
            "vitals_criteria": {"spo2_below": 92, "rr_above": 24},
            "treatment_prevents": ["adrenaline", "epinephrine", "hydrocortisone", "intubation", "tracheostomy"],
            "urgency": "critical",
            "agent_message": "Doctor! Lips and tongue are massively swollen! Patient is developing stridor — can barely talk! SpO2 falling to {spo2}%. We may need to secure the airway!",
            "trajectory_effect": "critical",
        },
    ],

    "orthopedics": [
        {
            "name": "Fat Embolism Syndrome",
            "description": "Fat embolism from long-bone fracture causing respiratory failure, neurological symptoms, and petechial rash",
            "probability_base": 0.08,
            "time_window": (720, 2880),
            "vitals_criteria": {"spo2_below": 90, "hr_above": 110, "rr_above": 24},
            "treatment_prevents": ["early_fixation", "fracture_stabilization", "oxygen", "supportive_care"],
            "urgency": "critical",
            "agent_message": "Doctor! Post-fracture patient suddenly confused, tachypneic, SpO2 dropped to {spo2}%! Petechial rash on chest and conjunctivae. Classic fat embolism syndrome!",
            "trajectory_effect": "critical",
        },
        {
            "name": "Compartment Syndrome",
            "description": "Elevated intra-compartmental pressure after fracture/crush injury threatening limb viability",
            "probability_base": 0.10,
            "time_window": (60, 480),
            "vitals_criteria": {"hr_above": 100},
            "treatment_prevents": ["fasciotomy", "cast_bivalve", "cast_removal", "elevation", "orthopedic_consult"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient's limb pain is excruciating and out of proportion! 5 P's — Pain on passive stretch, paresthesias! Compartment is rock hard. We need fasciotomy before we lose the limb!",
            "trajectory_effect": "deteriorating",
        },
        {
            "name": "Deep Vein Thrombosis / Pulmonary Embolism",
            "description": "DVT with embolization to pulmonary vasculature after immobilization",
            "probability_base": 0.08,
            "time_window": (360, 4320),
            "vitals_criteria": {"hr_above": 110, "spo2_below": 92, "rr_above": 22},
            "treatment_prevents": ["dvt_prophylaxis", "enoxaparin", "heparin", "early_mobilization", "compression_stockings"],
            "urgency": "critical",
            "agent_message": "Doctor! Patient suddenly short of breath, chest pain, HR is {hr}! SpO2 dropped to {spo2}%. Calf is swollen. Post-immobilization — I think this is a PE!",
            "trajectory_effect": "critical",
        },
    ],
}

# ---------------------------------------------------------------------------
# Distraction / cross-patient interruptions (specialty-agnostic)
# ---------------------------------------------------------------------------
DISTRACTION_EVENTS: list[dict] = [
    {
        "name": "Another Patient Emergency",
        "description": "Nurse asks for help with another patient crashing in the ward",
        "min_time": 30,
        "max_time": 180,
        "probability": 0.03,
        "agent_message": "Doctor, sorry to interrupt — the patient in bed 4 is having chest pain and looks unwell. Can you come quickly? I know you're busy here but...",
        "urgency": "urgent",
    },
    {
        "name": "Relative Confrontation",
        "description": "Angry family member demands to speak with the doctor",
        "min_time": 20,
        "max_time": 120,
        "probability": 0.04,
        "agent_message": "Doctor, the patient's family is at the nursing station and they're very upset. They want to know why nothing has been done. The son is threatening to complain to the superintendent.",
        "urgency": "urgent",
    },
    {
        "name": "Phone Call from Lab",
        "description": "Lab technician calls with a panic value that needs immediate attention",
        "min_time": 30,
        "max_time": 180,
        "probability": 0.05,
        "agent_message": "Doctor, urgent call from the lab — they've flagged a critical value on one of your patient's samples. They need a verbal acknowledgement and want to know if you want to repeat the test.",
        "urgency": "urgent",
    },
    {
        "name": "Equipment Failure",
        "description": "Critical equipment malfunctions",
        "min_time": 15,
        "max_time": 120,
        "probability": 0.03,
        "agent_message": "Doctor, the pulse oximeter seems to be giving erratic readings and the backup monitor is also not working. Should we shift the patient to a bed with a working monitor?",
        "urgency": "urgent",
    },
    {
        "name": "Blood Bank Delay",
        "description": "Blood bank notifies of delay in cross-matched blood",
        "min_time": 30,
        "max_time": 120,
        "probability": 0.04,
        "agent_message": "Doctor, blood bank called — the requested blood group is in short supply. They can arrange one unit but it will take another 2 hours. Should we call for donors?",
        "urgency": "urgent",
    },
]


# ---------------------------------------------------------------------------
# ComplicationEngine
# ---------------------------------------------------------------------------

class ComplicationEngine:
    """Generates probabilistic complications, time-based triggers, and urgent interruptions.

    This engine is called by the orchestrator after each student action (after the
    CaseStateManager has advanced time and evolved vitals). It evaluates every
    possible complication for the current case, calculates time-dependent probability,
    and returns any triggered events as SimulationEvent objects.

    Design principles:
        - Complications are CLINICALLY REALISTIC, not random
        - Probability INCREASES over time if the condition is untreated
        - Correct treatment PREVENTS complications
        - Each specialty has its own complication profile
        - Distractions and cross-patient interruptions add cognitive load
    """

    def __init__(self, case_data: dict, state_manager: CaseStateManager):
        self.case_data = case_data
        self.state_manager = state_manager

        # Extract case identity
        self.specialty: str = (case_data.get("specialty") or "emergency").lower().strip()
        self.diagnosis: str = (case_data.get("diagnosis") or case_data.get("final_diagnosis") or "").lower().strip()
        self.difficulty: str = (case_data.get("difficulty") or "intermediate").lower().strip()

        # Resolve which complications are possible for this case
        self.possible_complications: list[dict] = self._get_specialty_complications(
            self.specialty, self.diagnosis
        )

        # Track which complications have already fired (no repeats)
        self.fired_complications: set[str] = set()

        # Track distraction events already delivered
        self.fired_distractions: set[str] = set()

        # Internal event ID counter — starts high to avoid collision with state manager
        self._next_event_id: int = 5000

        # Difficulty multiplier — harder cases have more frequent complications
        self._difficulty_multiplier: float = {
            "beginner": 0.5,
            "intermediate": 1.0,
            "advanced": 1.5,
        }.get(self.difficulty, 1.0)

        logger.info(
            f"ComplicationEngine initialized: specialty={self.specialty}, "
            f"diagnosis={self.diagnosis}, difficulty={self.difficulty}, "
            f"possible_complications={len(self.possible_complications)}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_complications(
        self,
        elapsed_minutes: int,
        current_vitals: dict,
        treatments: list,
        investigations: dict,
    ) -> list[SimulationEvent]:
        """Evaluate all possible complications and return any that trigger.

        Called by the orchestrator after each student action, AFTER the state manager
        has advanced time and evolved vitals.

        Args:
            elapsed_minutes: Current simulation clock.
            current_vitals: Current patient vitals dict from state manager.
            treatments: List of TreatmentRecord objects (or dicts) of treatments given so far.
            investigations: Dict of ordered investigations from state manager.

        Returns:
            List of SimulationEvent objects for any triggered complications/interruptions.
        """
        triggered_events: list[SimulationEvent] = []

        # Collect all treatment descriptions for matching
        treatment_descriptions = self._collect_treatment_keywords(treatments)

        # 1. Check each possible clinical complication
        for complication in self.possible_complications:
            comp_name = complication["name"]

            # Skip if already fired
            if comp_name in self.fired_complications:
                continue

            # Check if we're in the time window
            min_t, max_t = complication["time_window"]
            if elapsed_minutes < min_t or elapsed_minutes > max_t:
                continue

            # Check if preventive treatment was given
            treated = self._is_treated(complication, treatment_descriptions)

            # Calculate probability
            probability = self._calculate_probability(
                complication, elapsed_minutes, treated, current_vitals
            )

            # Roll the dice
            if random.random() < probability:
                event = self._generate_interruption(complication, current_vitals, elapsed_minutes)
                triggered_events.append(event)
                self.fired_complications.add(comp_name)

                # Escalate patient trajectory on the state manager
                self._escalate_trajectory(complication)

                logger.warning(
                    f"COMPLICATION TRIGGERED: {comp_name} at t={elapsed_minutes}min "
                    f"(probability was {probability:.3f})"
                )

        # 2. Check distraction / cross-patient interruptions
        distraction = self._check_distractions(elapsed_minutes)
        if distraction is not None:
            triggered_events.append(distraction)

        return triggered_events

    def get_possible_complications(self) -> list[dict]:
        """Return list of possible complications for external inspection (e.g., by evaluator).

        Returns a sanitized view without revealing exact probabilities to the student.
        """
        return [
            {
                "name": c["name"],
                "description": c["description"],
                "urgency": c["urgency"],
                "time_window": c["time_window"],
                "preventable_by": c["treatment_prevents"],
            }
            for c in self.possible_complications
        ]

    def get_fired_complications(self) -> list[str]:
        """Return names of complications that have already triggered."""
        return list(self.fired_complications)

    def force_complication(self, complication_name: str, elapsed_minutes: int, current_vitals: dict) -> Optional[SimulationEvent]:
        """Force-trigger a specific complication regardless of probability.

        Used by the evaluator agent or orchestrator for pedagogical purposes —
        e.g., to test whether the student can handle a specific emergency.

        Args:
            complication_name: Exact name of the complication to trigger.
            elapsed_minutes: Current simulation time.
            current_vitals: Current vitals dict.

        Returns:
            SimulationEvent if the complication exists and hasn't fired yet, else None.
        """
        for complication in self.possible_complications:
            if complication["name"] == complication_name and complication_name not in self.fired_complications:
                event = self._generate_interruption(complication, current_vitals, elapsed_minutes)
                self.fired_complications.add(complication_name)
                self._escalate_trajectory(complication)
                logger.warning(f"COMPLICATION FORCE-TRIGGERED: {complication_name} at t={elapsed_minutes}min")
                return event

        logger.warning(f"Cannot force complication '{complication_name}' — not found or already fired.")
        return None

    # ------------------------------------------------------------------
    # Specialty complication resolution
    # ------------------------------------------------------------------

    def _get_specialty_complications(self, specialty: str, diagnosis: str) -> list[dict]:
        """Resolve which complications are possible for this case.

        Strategy:
            1. Look up exact specialty match in SPECIALTY_COMPLICATIONS
            2. If not found, fall back to "emergency" (generic acute complications)
            3. Filter by diagnosis keywords if they narrow the complication set
            4. Always include a subset of generic emergency complications
        """
        complications: list[dict] = []

        # Primary specialty complications
        primary = SPECIALTY_COMPLICATIONS.get(specialty, [])
        complications.extend(primary)

        # If specialty not found, use emergency as fallback
        if not primary and specialty != "emergency":
            logger.info(f"No specific complications for specialty '{specialty}', using emergency fallback")
            complications.extend(SPECIALTY_COMPLICATIONS.get("emergency", []))

        # Add a few cross-cutting emergency complications if not already covered
        # (septic shock can happen in any specialty, anaphylaxis from any drug)
        emergency_crosscuts = ["Anaphylaxis", "Hemorrhagic Shock"]
        if specialty != "emergency":
            for ec_comp in SPECIALTY_COMPLICATIONS.get("emergency", []):
                if ec_comp["name"] in emergency_crosscuts and ec_comp["name"] not in [c["name"] for c in complications]:
                    # Add with reduced base probability since it's cross-specialty
                    cross_comp = dict(ec_comp)
                    cross_comp["probability_base"] = ec_comp["probability_base"] * 0.3
                    complications.append(cross_comp)

        # Diagnosis-specific filtering: boost probability for relevant complications
        complications = self._filter_by_diagnosis(complications, diagnosis)

        return complications

    def _filter_by_diagnosis(self, complications: list[dict], diagnosis: str) -> list[dict]:
        """Boost or reduce complication probabilities based on the specific diagnosis.

        For example, if the diagnosis contains "STEMI", boost cardiogenic shock.
        If it contains "dengue", boost hemorrhagic manifestations.
        """
        if not diagnosis:
            return complications

        # Diagnosis keyword -> complication name -> probability multiplier
        diagnosis_boosts: dict[str, dict[str, float]] = {
            "stemi": {"Cardiogenic Shock": 2.0, "Ventricular Tachycardia": 1.8, "Cardiac Arrest — VF/Pulseless VT": 1.5},
            "nstemi": {"Cardiogenic Shock": 1.3, "Acute Heart Failure / Pulmonary Edema": 1.5},
            "heart failure": {"Acute Heart Failure / Pulmonary Edema": 2.0, "Cardiogenic Shock": 1.5},
            "pneumonia": {"Respiratory Failure — Type 1": 1.8, "Septic Shock": 1.5, "ARDS Development": 1.5},
            "copd": {"Respiratory Failure — Type 1": 1.5},
            "asthma": {"Respiratory Failure — Type 1": 2.0},
            "dengue": {"Dengue Hemorrhagic Manifestations": 2.5, "Disseminated Intravascular Coagulation": 1.5},
            "malaria": {"Septic Shock": 1.3, "Multi-Organ Dysfunction": 1.5},
            "sepsis": {"Septic Shock": 2.0, "Multi-Organ Dysfunction": 1.8, "Disseminated Intravascular Coagulation": 1.5},
            "meningitis": {"Raised ICP — Deterioration": 1.8, "Status Epilepticus": 1.5, "Cerebral Herniation": 1.3},
            "stroke": {"Cerebral Herniation": 2.0, "Raised ICP — Deterioration": 1.8, "Status Epilepticus": 1.3},
            "cirrhosis": {"Variceal Rupture": 2.0, "Hepatic Encephalopathy": 2.0, "Spontaneous Bacterial Peritonitis": 2.0},
            "gi bleed": {"Massive Upper GI Bleed": 2.5, "Variceal Rupture": 1.5},
            "dka": {"Cerebral Edema in DKA": 2.0, "Severe Hypoglycemia — Seizure/Coma": 1.5},
            "thyroid storm": {"Thyroid Storm": 2.5},
            "addison": {"Adrenal Crisis": 2.5},
            "pre-eclampsia": {"Eclampsia": 2.5, "DIC in Obstetrics": 1.5},
            "eclampsia": {"Eclampsia": 2.0, "DIC in Obstetrics": 1.8},
            "leukemia": {"Tumor Lysis Syndrome": 2.0, "Febrile Neutropenia — Sepsis": 2.0},
            "lymphoma": {"Tumor Lysis Syndrome": 2.0, "Febrile Neutropenia — Sepsis": 1.5},
            "fracture": {"Fat Embolism Syndrome": 2.0, "Compartment Syndrome": 1.8, "Deep Vein Thrombosis / Pulmonary Embolism": 1.5},
            "ckd": {"Hyperkalemia — Cardiac Arrest": 2.0, "Flash Pulmonary Edema": 1.8, "Uremic Encephalopathy": 1.5},
            "aki": {"Hyperkalemia — Cardiac Arrest": 1.8, "Flash Pulmonary Edema": 1.5},
            "sjs": {"SJS Progression to TEN": 2.5, "Secondary Sepsis from Skin": 1.8},
            "nms": {"Neuroleptic Malignant Syndrome": 2.5},
        }

        # Find all matching boosts
        applicable_boosts: dict[str, float] = {}
        for keyword, boosts in diagnosis_boosts.items():
            if keyword in diagnosis:
                for comp_name, multiplier in boosts.items():
                    # Take the highest boost if multiple keywords match
                    if comp_name not in applicable_boosts or multiplier > applicable_boosts[comp_name]:
                        applicable_boosts[comp_name] = multiplier

        # Apply boosts
        if applicable_boosts:
            boosted = []
            for comp in complications:
                comp_copy = dict(comp)
                if comp_copy["name"] in applicable_boosts:
                    comp_copy["probability_base"] = min(
                        0.5,  # cap at 50% base probability
                        comp_copy["probability_base"] * applicable_boosts[comp_copy["name"]]
                    )
                boosted.append(comp_copy)
            return boosted

        return complications

    # ------------------------------------------------------------------
    # Probability calculation
    # ------------------------------------------------------------------

    def _calculate_probability(
        self,
        complication: dict,
        elapsed: int,
        treated: bool,
        current_vitals: dict,
    ) -> float:
        """Calculate the probability of a complication firing at this tick.

        The probability model:
            1. Start with probability_base
            2. Apply time curve: probability rises as we move through the time window
               Peak probability at 75% of the window, then plateaus
            3. Apply difficulty multiplier
            4. If treated: multiply by 0.05 (95% reduction — not zero, because
               treatment doesn't guarantee prevention)
            5. Apply vitals criteria: if vitals match danger thresholds, boost 2x
            6. Cap at 0.6 per tick to avoid certainty

        Returns:
            Probability as a float in [0.0, 0.6].
        """
        base = complication["probability_base"]
        min_t, max_t = complication["time_window"]
        window_duration = max(max_t - min_t, 1)

        # Time curve: ramps up linearly to peak at 75% of window
        time_into_window = elapsed - min_t
        peak_point = window_duration * 0.75
        if time_into_window <= peak_point:
            time_factor = time_into_window / peak_point  # 0.0 -> 1.0
        else:
            time_factor = 1.0  # plateau after peak

        # Per-tick probability (base * time_factor gives the cumulative-ish probability)
        # We normalize so that each tick is a small chance
        probability = base * time_factor

        # Difficulty multiplier
        probability *= self._difficulty_multiplier

        # Treatment reduction
        if treated:
            probability *= 0.05  # 95% reduction

        # Vitals criteria boost
        vitals_boost = self._evaluate_vitals_criteria(complication, current_vitals)
        probability *= vitals_boost

        # Cap probability per tick
        probability = min(0.6, max(0.0, probability))

        return probability

    def _evaluate_vitals_criteria(self, complication: dict, current_vitals: dict) -> float:
        """Evaluate how much the current vitals boost this complication's probability.

        Each matching criterion adds a 1.5x multiplier (compounding).
        No matching criteria returns 1.0 (no change).
        """
        criteria = complication.get("vitals_criteria", {})
        if not criteria:
            return 1.0

        multiplier = 1.0

        for criterion, threshold in criteria.items():
            if criterion == "bp_systolic_below":
                if current_vitals.get("bp_systolic", 120) < threshold:
                    multiplier *= 1.5
            elif criterion == "bp_systolic_above":
                if current_vitals.get("bp_systolic", 120) > threshold:
                    multiplier *= 1.5
            elif criterion == "hr_above":
                if current_vitals.get("hr", 80) > threshold:
                    multiplier *= 1.5
            elif criterion == "hr_below":
                if current_vitals.get("hr", 80) < threshold:
                    multiplier *= 1.5
            elif criterion == "spo2_below":
                if current_vitals.get("spo2", 98) < threshold:
                    multiplier *= 1.5
            elif criterion == "rr_above":
                if current_vitals.get("rr", 16) > threshold:
                    multiplier *= 1.5
            elif criterion == "temp_above":
                if current_vitals.get("temp", 37.0) > threshold:
                    multiplier *= 1.5
            elif criterion == "temp_below":
                if current_vitals.get("temp", 37.0) < threshold:
                    multiplier *= 1.5

        return multiplier

    # ------------------------------------------------------------------
    # Treatment matching
    # ------------------------------------------------------------------

    def _collect_treatment_keywords(self, treatments: list) -> set[str]:
        """Extract a set of lowercase keywords from all administered treatments.

        Handles both TreatmentRecord objects and plain dicts.
        """
        keywords: set[str] = set()
        for tx in treatments:
            if hasattr(tx, "description"):
                desc = tx.description
            elif isinstance(tx, dict):
                desc = tx.get("description", "")
            else:
                desc = str(tx)

            # Tokenize the treatment description into keywords
            desc_lower = desc.lower()
            # Split on common separators
            for token in desc_lower.replace(",", " ").replace(".", " ").replace("-", "_").replace("/", " ").split():
                token = token.strip()
                if len(token) > 2:  # skip very short tokens
                    keywords.add(token)

            # Also keep the full description as a keyword for phrase matching
            keywords.add(desc_lower)

        return keywords

    def _is_treated(self, complication: dict, treatment_keywords: set[str]) -> bool:
        """Check if any preventive treatment for this complication has been given.

        Uses fuzzy keyword matching: if any token from treatment_prevents appears
        in the collected treatment keywords, we consider it treated.
        """
        prevents = complication.get("treatment_prevents", [])
        for prevent_keyword in prevents:
            prevent_lower = prevent_keyword.lower().replace("-", "_")
            # Direct match
            if prevent_lower in treatment_keywords:
                return True
            # Partial match: check if any treatment keyword contains this keyword
            for tk in treatment_keywords:
                if prevent_lower in tk or tk in prevent_lower:
                    return True
        return False

    # ------------------------------------------------------------------
    # Event generation
    # ------------------------------------------------------------------

    def _generate_interruption(
        self,
        complication: dict,
        current_vitals: dict,
        elapsed_minutes: int,
    ) -> SimulationEvent:
        """Create a SimulationEvent from a triggered complication.

        The agent_message is formatted with current vital sign values to make
        the interruption feel clinically realistic and grounded in real numbers.
        """
        # Format the agent message with current vitals
        message = complication["agent_message"].format(
            bp_systolic=current_vitals.get("bp_systolic", "??"),
            bp_diastolic=current_vitals.get("bp_diastolic", "??"),
            hr=current_vitals.get("hr", "??"),
            rr=current_vitals.get("rr", "??"),
            spo2=current_vitals.get("spo2", "??"),
            temp=current_vitals.get("temp", "??"),
        )

        # Determine event type based on urgency
        if complication["urgency"] == "critical":
            event_type = "critical_complication"
        else:
            event_type = "urgent_complication"

        event = SimulationEvent(
            event_id=f"comp-{self._next_event_id}",
            timestamp=elapsed_minutes,
            event_type=event_type,
            title=f"COMPLICATION: {complication['name']}",
            description=message,
            agent_type="nurse",
        )
        self._next_event_id += 1

        # Also register this event on the state manager so it appears in the timeline
        self.state_manager.events.append(event)

        return event

    # ------------------------------------------------------------------
    # Trajectory escalation
    # ------------------------------------------------------------------

    def _escalate_trajectory(self, complication: dict):
        """Escalate the patient trajectory on the state manager based on the complication.

        Critical complications push straight to CRITICAL.
        Urgent complications push to DETERIORATING if currently STABLE/IMPROVING.
        """
        effect = complication.get("trajectory_effect", "deteriorating")

        if effect == "critical":
            self.state_manager.trajectory = PatientTrajectory.CRITICAL
        elif effect == "deteriorating":
            if self.state_manager.trajectory in (PatientTrajectory.STABLE, PatientTrajectory.IMPROVING):
                self.state_manager.trajectory = PatientTrajectory.DETERIORATING

    # ------------------------------------------------------------------
    # Distraction events
    # ------------------------------------------------------------------

    def _check_distractions(self, elapsed_minutes: int) -> Optional[SimulationEvent]:
        """Check if a distraction / cross-patient interruption should fire.

        Only one distraction per session to avoid being annoying. Distractions
        increase cognitive load and test the student's ability to prioritize.

        Returns:
            A SimulationEvent if a distraction triggers, else None.
        """
        # Maximum one distraction per session
        if len(self.fired_distractions) >= 2:
            return None

        for distraction in DISTRACTION_EVENTS:
            d_name = distraction["name"]
            if d_name in self.fired_distractions:
                continue

            if elapsed_minutes < distraction["min_time"] or elapsed_minutes > distraction["max_time"]:
                continue

            # Probability adjusted by difficulty
            prob = distraction["probability"] * self._difficulty_multiplier

            if random.random() < prob:
                event = SimulationEvent(
                    event_id=f"dist-{self._next_event_id}",
                    timestamp=elapsed_minutes,
                    event_type="distraction",
                    title=f"INTERRUPTION: {d_name}",
                    description=distraction["agent_message"],
                    agent_type="nurse",
                )
                self._next_event_id += 1
                self.fired_distractions.add(d_name)

                # Register on state manager timeline
                self.state_manager.events.append(event)

                logger.info(f"DISTRACTION TRIGGERED: {d_name} at t={elapsed_minutes}min")
                return event

        return None

    # ------------------------------------------------------------------
    # Summary / debug
    # ------------------------------------------------------------------

    def get_engine_summary(self) -> str:
        """Return a summary of the complication engine state for debugging / logging."""
        lines = [
            f"ComplicationEngine Summary:",
            f"  Specialty: {self.specialty}",
            f"  Diagnosis: {self.diagnosis}",
            f"  Difficulty: {self.difficulty} (multiplier: {self._difficulty_multiplier})",
            f"  Possible complications: {len(self.possible_complications)}",
            f"  Fired complications: {self.fired_complications or 'none'}",
            f"  Fired distractions: {self.fired_distractions or 'none'}",
            f"  Possible complication names:",
        ]
        for c in self.possible_complications:
            lines.append(
                f"    - {c['name']} (base_p={c['probability_base']:.2f}, "
                f"window={c['time_window']}, urgency={c['urgency']})"
            )
        return "\n".join(lines)
