# Clinical Mind - Automated Demo

**Separate automation for hackathon demo recording**

This is a standalone Puppeteer script that runs the Clinical Mind demo autonomously while you record your screen. Perfect for hackathon presentations where you need a smooth, professional demo without fumbling with medical terminology.

## 🎯 Why Automated Demo?

- **Industry Standard**: Most winning hackathon teams use scripted demos
- **Consistent**: Same perfect flow every time
- **Professional**: No typos, no confusion, smooth pacing
- **Separate**: Doesn't interfere with main project code
- **Judges can still test**: Main app at `/simulation` works independently

## 🚀 Quick Start

### 1. Setup (One Time)
```bash
cd demo-automation
npm install
```

### 2. Ensure App is Running
```bash
# Terminal 1 - Backend
cd ../backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd ../frontend
npm start
```

### 3. Run Demo
```bash
# Terminal 3 - Demo
cd demo-automation
npm run demo
```

### 4. Record Your Screen
- Start recording when you see "📹 Start your screen recording software now!"
- The script will:
  - Open browser automatically
  - Navigate through the entire case
  - Type messages with realistic speed
  - Click buttons at the right time
  - Show all features systematically
- Stop recording when you see "✅ Demo completed successfully!"

## 📝 Available Scripts

- `npm run demo` - Runs demo using /demo page (predictable)
- `npm run demo:leptos` - Runs full simulation with Leptospirosis
- `npm run demo:nmosd` - Runs NMOSD case demo (if needed)

## 🎬 What Gets Demonstrated

1. **Multi-Agent System** - All 5 agents responding
2. **Hinglish Authenticity** - Patient/family speaking naturally
3. **Clinical Workflow** - History → Examination → Investigation → Diagnosis
4. **Real-time Vitals** - Shows critical values updating
5. **Team Collaboration** - Huddle feature with all agents
6. **Educational Value** - Senior doctor providing guidance
7. **Investigation System** - Ordering and checking lab results
8. **Treatment Management** - Starting appropriate therapy
9. **Patient Deterioration** - Urgency indicators

## ⚙️ Customization

Edit timing in `demo.js`:
```javascript
const TYPING_DELAY = 70;   // Speed of typing (ms)
const READ_DELAY = 2500;    // Time to "read" responses
const SHORT_PAUSE = 1000;   // Between actions
const LONG_PAUSE = 3500;    // After important moments
```

## 🔧 Troubleshooting

**Browser doesn't open:**
- Install Chrome/Chromium: `npx puppeteer browsers install chrome`

**Selectors not found:**
- Check if UI changed: Update selectors in demo.js
- Add more wait time: Increase timeouts

**Too fast/slow:**
- Adjust timing constants at top of demo.js

**Want different case flow:**
- Edit the messages array in demo.js
- Change the sequence of actions

## 📂 Structure

```
demo-automation/          # Separate from main project
├── package.json          # Dependencies
├── demo.js              # Main demo script (uses /demo)
├── demo-leptospirosis.js # Alternative full simulation
└── README.md            # This file
```

## 🚫 Not Included in Main Project

This folder is completely separate and can be:
- Deleted after hackathon
- Kept for future demos
- Not committed to main repo

The main Clinical Mind app works independently without this automation.

## 🏆 Tips for Recording

1. **Clean Desktop** - Hide personal files/apps
2. **Full Screen Browser** - F11 for professional look
3. **Good Internet** - For smooth API responses
4. **Multiple Takes** - Record 2-3 times, pick best
5. **Add Voiceover** - Explain features while it runs

## 📹 Recommended Recording Software

- **OBS Studio** (Free, all platforms)
- **QuickTime** (Mac built-in)
- **Windows Game Bar** (Win+G)
- **Loom** (Free tier available)

---

**Note:** This is for demo purposes only. Judges can test the real app at `localhost:3000/simulation`