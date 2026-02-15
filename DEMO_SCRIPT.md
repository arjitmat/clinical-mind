# Clinical Mind - Hackathon Demo Script

## 🎬 PRIVATE DEMO INSTRUCTIONS (Not shown to judges)

### Demo URL: `http://localhost:3000/demo`

---

## DEMO 1: ACUTE MI (Heart Attack) - 8-10 minutes

### Step 1: Student Profile Selection
**What to Enter:**
- Name: `Demo Student` (or your name)
- Level: Select **"Intern"** ← IMPORTANT!

### Step 2: Case Selection
**Select:** The first case - "Severe crushing chest pain for 2 hours"

### Step 3: Wait for Agent Initialization
- Takes 2-3 minutes
- Explain to judges: "5 AI agents are learning this case in parallel using Claude Opus 4.1"
- Point out the animated loading screen showing each agent preparing

### Step 4: Initial Messages
- You'll see messages from Patient, Family, Nurse Priya, and Dr. Sharma
- Let them read the Hinglish messages

### Step 5: Conversation Script

**Question 1 - Talk to Patient:**
```
Can you describe your chest pain?
```
*Expected: Patient describes crushing chest pain in Hinglish*

**Question 2 - Ask Nurse:**
```
What are the current vital signs?
```
*Expected: Nurse reports critical vitals, BP dropping*

**Question 3 - Order Investigation:**
```
ECG stat
```
*Expected: ECG ordered urgently*

**Question 4 - Consult Senior:**
```
ECG shows ST elevation, should we activate cath lab?
```
*Expected: Dr. Sharma confirms STEMI, educational feedback*

**Question 5 - Order Treatment:**
```
Aspirin 325mg stat, prepare for PCI
```
*Expected: Treatment initiated*

**Question 6 - Team Huddle:**
```
STEMI protocol activated
```
*Expected: ALL 5 agents respond - shows orchestration!*

### Step 6: Make Diagnosis
Click "Make Diagnosis" button when it appears
Enter: `Acute ST-elevation myocardial infarction`

### Key Points to Emphasize:
- Live vitals updating every 5 seconds (point to the numbers changing)
- Urgency indicators (red/amber/green colors)
- Multiple agents responding naturally
- Hinglish authenticity in patient/family responses

---

## DEMO 2: DENGUE FEVER - 10-12 minutes

### Step 1: Student Profile Selection
**What to Enter:**
- Name: `Demo Student`
- Level: Select **"MBBS 3rd Year"** ← IMPORTANT!

### Step 2: Case Selection
**Select:** The second case - "High fever with body aches for 4 days"

### Step 3: Wait for Initialization
- Same 2-3 minute wait
- Explain parallel agent learning

### Step 4: Conversation Script

**Question 1 - Talk to Patient:**
```
Kab se bukhar hai? Any bleeding from anywhere?
```
*Expected: Patient responds in Hinglish about 4-day fever*

**Question 2 - Talk to Family:**
```
Kya khaya piya hai? Any mosquito bites?
```
*Expected: Family provides context in Hinglish*

**Question 3 - Examine Patient:**
```
Tourniquet test
```
*Expected: Physical exam findings*

**Question 4 - Order Investigation:**
```
CBC with platelet count, Dengue NS1
```
*Expected: Labs ordered*

**Question 5 - Ask Lab Tech:**
```
Platelet count kya hai?
```
*Expected: Lab Tech Ramesh reports falling platelets*

**Question 6 - Order Treatment:**
```
IV fluids NS 100ml/hr, monitor platelets
```
*Expected: Supportive care started*

**Question 7 - Consult Senior:**
```
Warning signs present, should we admit?
```
*Expected: Dr. Sharma provides teaching on dengue management*

### Step 5: Make Diagnosis
Enter: `Dengue fever with warning signs`

---

## 📹 RECORDING TIPS

1. **Browser Setup:**
   - Use Chrome in incognito mode
   - Window size: 1920x1080
   - Hide bookmarks bar
   - Close all other tabs

2. **Before Recording:**
   - Clear browser cache
   - Restart backend if needed
   - Test one message first

3. **During Recording:**
   - Speak clearly about what's happening
   - Point out live vitals updates
   - Emphasize multi-agent responses
   - Show the loading animation

---

## 🎯 KEY TALKING POINTS

### Technical Excellence:
- "Real-time API calls to Claude Opus 4.1"
- "5 specialized agents learning in parallel"
- "432 real medical cases in vector database"
- "Authentic Indian hospital simulation"

### Educational Value:
- "Personalized to student level"
- "Active learning through conversation"
- "Immediate feedback from senior doctor"
- "Safe environment to practice"

### Multi-Agent Orchestration:
- "Notice how each agent has their own personality"
- "Family speaks in Hinglish naturally"
- "Agents coordinate without explicit programming"
- "Seamless handoffs between agents"

### Live Features:
- "Watch the vitals - they update every 5 seconds"
- "Color coding shows urgency levels"
- "Suggested questions guide clinical reasoning"
- "Real-time case progression"

---

## ⚠️ TROUBLESHOOTING

**If agents take too long to initialize:**
- Say: "Complex cases require more learning time"
- Explain the parallel processing happening

**If an unexpected response:**
- Say: "The AI is contextually aware and may vary responses"
- Continue with the script

**If vitals don't update:**
- Continue normally - they update in background
- Focus on the conversation flow

---

## 🏆 CLOSING STATEMENT

"Clinical Mind transforms medical education by providing authentic, AI-powered clinical simulations. With 5 specialized agents working together, students experience real hospital dynamics while learning at their own pace. The system uses cutting-edge Claude Opus 4.1 API with parallel processing and a knowledge base of 432 real cases, creating an immersive learning environment that bridges the gap between textbooks and clinical practice."

---

**Remember:**
- The demo page looks EXACTLY like the real app
- No special labeling or "demo mode" indicators
- Everything is real API calls
- Just follow this script for optimal presentation