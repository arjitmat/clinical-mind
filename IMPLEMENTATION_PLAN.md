# Clinical-Mind: Multi-Agent Hospital Simulator — Implementation Plan

## Project Vision
A realistic Indian hospital simulation for medical students where multiple AI agents (Patient, Nurse, Senior Doctor) dynamically learn per case, interact with each other, and create a time-progressing clinical scenario — NOT a chatbot.

## What Exists (Completed)
- **Backend agents**: base_agent.py, patient_agent.py, nurse_agent.py, senior_agent.py
- **Knowledge builder**: knowledge_builder.py with RAG + Claude Opus synthesis, source grounding rules, confidence classification
- **Orchestrator**: orchestrator.py — basic session management, routes student actions to single agents
- **API routes**: agents.py — /initialize, /action, /vitals endpoints
- **Frontend**: CaseInterface.tsx with agent chat sidebar, 3 animated SVG avatars, AgentMessage component
- **Medical corpus**: 142 verified Indian cases across 14 specialties (real sources: JAPI, ICMR, API, IAP, FOGSI, etc.)
- **RAG system**: ChromaDB vector store, MedicalRetriever, CaseGenerator
- **Landing page**: Landing.tsx with specialty cards (but NO student onboarding)
- **useApi.ts**: All agent API functions exist

## Architecture Overview
```
Frontend (React + TypeScript)
├── Landing.tsx          — Hero + Student Onboarding (level/topic selection)
├── CaseInterface.tsx    — Main simulation interface
│   ├── Case panel       — Patient card, vitals (LIVE), stages, diagnosis
│   ├── Simulation panel — Timeline events, ward activity
│   └── Chat sidebar     — Multi-agent conversations + team interactions
├── Avatars              — PatientAvatar, NurseAvatar, SeniorDoctorAvatar (SVG animated)
└── useApi.ts            — All API hooks

Backend (FastAPI + Python)
├── api/agents.py        — HTTP endpoints
├── core/agents/
│   ├── base_agent.py           — Abstract agent with Claude Opus extended thinking
│   ├── patient_agent.py        — Hinglish, distress levels, realistic Indian patient
│   ├── nurse_agent.py          — Clinical protocols, NLEM drugs, govt hospital reality
│   ├── senior_agent.py         — Socratic teaching, NEET-PG, progressive hints
│   ├── knowledge_builder.py    — RAG + Claude synthesis with source grounding
│   ├── orchestrator.py         — Session management, multi-agent coordination
│   ├── case_state_manager.py   — [NEW] Time, vitals evolution, investigation lifecycle
│   ├── treatment_engine.py     — [NEW] Drug effects, contraindications, outcomes
│   └── clinical_validator.py   — [NEW] Safety checks, dangerous action detection
└── core/rag/                   — ChromaDB, retriever, generator, scraper
```

---

## Phase 1: Case State Manager (`case_state_manager.py`)
**Purpose**: Make the simulation TIME-AWARE. Vitals change, investigations take time, patient can improve or deteriorate.

### Components:
1. **SimulationClock**: Tracks elapsed time in simulation (1 student action ≈ 5-15 min sim time depending on action type)
2. **VitalsEngine**: Models vital sign evolution based on:
   - Baseline vitals from case data
   - Current condition trajectory (stable/improving/deteriorating)
   - Treatment effects applied
   - Time elapsed
3. **InvestigationManager**: Tracks ordered investigations with realistic turnaround:
   - CBC, RFT, LFT, blood sugar: 2-4 hours (routine) / 30 min (urgent)
   - Blood culture: 24-48 hours
   - X-ray: 30 min
   - CT/MRI: may need referral (not available in all hospitals)
   - Troponin, D-dimer: 1-2 hours
   - ABG: 15-30 min
   - Results revealed only AFTER turnaround time passes
4. **PatientStateTracker**: Tracks clinical trajectory:
   - `stable` → `improving` (correct treatment) or `deteriorating` (wrong/no treatment)
   - Generates clinical events (new symptoms, complications) based on trajectory
   - Time-based deterioration if critical condition untreated

### Key behaviors:
- Each student action advances the simulation clock
- Vitals update with each tick (subtle changes, not random)
- Investigation results queue up and are delivered when ready
- Patient state changes trigger agent reactions (nurse alerts, senior concern)

---

## Phase 2: Treatment Engine (`treatment_engine.py`)
**Purpose**: Model the consequences of student's treatment decisions using Claude Opus.

### Components:
1. **TreatmentProcessor**: When student orders a treatment:
   - Validates drug availability (NLEM list for govt hospital)
   - Checks basic contraindications (renal dose adjustment, allergies from case data)
   - Calculates expected effect on vitals (e.g., IV fluids → BP stabilization)
   - Returns treatment_effect dict consumed by VitalsEngine
2. **DrugReference** (built dynamically via Opus):
   - For each case, Opus builds a focused drug reference from the knowledge base
   - Covers: first-line drugs for this condition, doses, contraindications, monitoring
   - Grounded in NLEM + corpus references
3. **OutcomeModeler**: Based on cumulative treatments:
   - Tracks whether student's management plan is appropriate
   - Feeds into case scoring at diagnosis submission

### Key behaviors:
- Student orders treatment → TreatmentEngine validates → VitalsEngine applies effect
- Wrong treatment → patient deteriorates (with clinical signs, not just numbers)
- Right treatment → patient improves (vitals normalize, symptoms reduce)
- Nurse and Senior react to treatment effects

---

## Phase 3: Clinical Validator (`clinical_validator.py`)
**Purpose**: Safety net — catch dangerous student actions before they harm the virtual patient.

### Components:
1. **DangerousActionDetector**: Flags critical errors:
   - Drug interaction with existing medications (from case history)
   - Contraindicated drugs (e.g., beta-blocker in decompensated heart failure)
   - Missing critical steps (e.g., ordering contrast CT without checking creatinine)
   - Dose errors (10x overdose patterns)
2. **ClinicalSafetyGate**: When danger detected:
   - Nurse Priya intervenes: "Doctor, just confirming — patient has [condition], should we still give [drug]?"
   - Senior Doctor may step in for critical errors: "Hold on, let's think about this..."
   - Student gets a teaching moment, not just a block

### Key behaviors:
- Runs on every treatment/investigation order
- Uses Claude Opus to assess clinical safety in context
- Returns safety_level: safe / caution / dangerous
- Triggers appropriate agent intervention

---

## Phase 4: Multi-Agent Interaction Protocol (Update `orchestrator.py`)
**Purpose**: Agents talk TO EACH OTHER, not just to the student. Like a real hospital.

### New interaction patterns:
1. **Nurse → Senior Escalation**: When nurse detects critical vitals or deterioration
   - Nurse: "Sir, patient's BP dropping to 80/50, should I start pressors?"
   - Senior responds with order AND teaching point for student
2. **Team Huddle**: At key decision points (after investigations return, after deterioration)
   - All 3 agents contribute perspectives
   - Patient describes new symptoms
   - Nurse reports latest vitals + observations
   - Senior synthesizes and guides student
3. **Background Events**: Nurse reports unprompted updates
   - "Doctor, patient is complaining of chest pain again"
   - "Lab results are back — CBC shows leukocytosis"
   - "Patient's family is asking about the condition"
4. **Agent Awareness**: Each agent's conversation includes summaries of what other agents said
   - Senior knows what patient told the student
   - Nurse knows what senior recommended
   - Patient reacts to treatments nurse administers

### New action types:
- `team_huddle` — All agents respond with their perspective
- `order_treatment` — Treatment action (triggers TreatmentEngine + Nurse response)
- `request_consultation` — Senior reviews entire case status

### Session state enrichment:
- `conversation_summary` — Rolling summary of key decisions/findings
- `pending_events` — Queue of simulation events waiting to fire
- `treatment_log` — All treatments ordered and their effects
- `investigation_log` — All investigations ordered, status, results

---

## Phase 5: Student Onboarding (Update `Landing.tsx`)
**Purpose**: Capture student level and topic preference BEFORE starting a case.

### Flow:
1. Student clicks "Start Case" on landing page
2. **Step 1 - Level Selection**:
   - "What year are you in?"
   - Options: MBBS 2nd Year (pre-clinical), MBBS 3rd Year (clinical), Intern, NEET-PG Aspirant, PG Resident
   - This maps to difficulty: beginner/intermediate/advanced
3. **Step 2 - Topic Selection**:
   - "What would you like to practice?"
   - Show specialty cards with case counts from actual corpus
   - Also option: "Surprise me" (random specialty)
4. **Step 3 - Scenario Context**:
   - Brief: "You're a junior doctor on night duty at [District Hospital/Medical College]. A patient arrives..."
   - Sets the simulation context (hospital type, resources available)
5. Navigate to `/case/new?specialty=X&difficulty=Y&level=Z`

### Data passed to backend:
- `student_level`: affects senior doctor's teaching style, language complexity
- `specialty`: case selection
- `difficulty`: case complexity
- `hospital_setting`: affects available resources in simulation

---

## Phase 6: Enhanced CaseInterface (Update `CaseInterface.tsx`)
**Purpose**: Full simulation experience with live updates, multi-agent interactions, and clinical workflow.

### New UI sections:
1. **Live Vitals Monitor** (top of case panel):
   - Real-time vital signs that update with each action
   - Color-coded: green (normal), yellow (borderline), red (critical)
   - Trend arrows (↑ rising, ↓ falling, → stable)
   - Polls `/agents/vitals/{session_id}` after each action
2. **Simulation Timeline** (between case panel and chat):
   - Chronological events: "00:00 — Patient arrives", "00:15 — Blood drawn", "02:30 — CBC results back"
   - Shows pending investigations with estimated time
   - Treatment actions logged
3. **Enhanced Action Bar** (replaces simple agent selector):
   - Clinical actions: History, Examine, Investigate, Treat, Consult
   - Each opens relevant sub-options or free text
   - `examine_patient` → triggers patient + nurse
   - `order_investigation` → shows available tests
   - `order_treatment` → treatment input with nurse confirmation
   - `team_huddle` → all agents respond
4. **Agent Interaction Feed**:
   - Shows agent-to-agent messages (nurse calling senior, patient complaining to nurse)
   - Visually distinct from student conversations (lighter background, smaller text)
   - Student can observe or join the conversation

### Enhanced chat behaviors:
- Typing indicators per agent
- Agent thinking visualization (brief "Analyzing vitals..." before response)
- Agent-to-agent messages appear automatically in feed
- Investigation results delivered as nurse messages when ready

---

## Phase 7: API Updates (`agents.py`)
### New endpoints:
- `POST /agents/treat` — Order treatment (validates via TreatmentEngine)
- `POST /agents/huddle` — Trigger team huddle
- `GET /agents/timeline/{session_id}` — Get simulation timeline events
- `GET /agents/investigations/{session_id}` — Get investigation status/results
- `POST /agents/advance-time` — Explicitly advance simulation clock (e.g., "wait for results")

### Updated endpoints:
- `POST /agents/action` — Now includes simulation clock update, pending events check
- `POST /agents/initialize` — Now accepts student_level, hospital_setting
- `GET /agents/vitals/{session_id}` — Now returns trend data + alerts

---

## Build Order (Sequential Dependencies)
```
1. case_state_manager.py     (no dependencies — pure state logic)
2. treatment_engine.py       (depends on: case_state_manager for vitals effects)
3. clinical_validator.py     (depends on: treatment_engine for drug checking)
4. orchestrator.py REWRITE   (depends on: all 3 above + existing agents)
5. agents.py UPDATE          (depends on: updated orchestrator)
6. useApi.ts UPDATE          (depends on: updated API routes)
7. Landing.tsx UPDATE        (no backend dependency — pure frontend)
8. CaseInterface.tsx UPDATE  (depends on: updated useApi)
9. Build + Test              (depends on: all above)
```

---

## Quality Gates
- Every backend file: `python -c "import ast; ast.parse(open('file.py').read())"` — must pass
- Frontend: `npm run build` — must compile with zero errors
- No placeholder data — all medical content from corpus or Opus synthesis
- No invented guidelines — source grounding rules enforced
- Indian hospital reality — resource constraints in every clinical decision

## Git Branch
All work on: `claude/clinical-mind-setup-1kk5p`
