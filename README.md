# Clinical-Mind

**Master clinical reasoning, one case at a time.**

An AI-powered clinical reasoning simulator that helps Indian medical students develop expert-level diagnostic thinking by exposing cognitive biases, providing Socratic feedback, and creating realistic case scenarios.

## Problem

Medical students can memorize and answer MCQs, but struggle with real clinical reasoning:
- **Invisible cognitive biases** (anchoring, premature closure, availability)
- **Can't explain reasoning** when attendings ask "Why?"
- **No practice under pressure** - freeze in real emergencies
- **Can't see knowledge connections** between concepts
- **Textbook cases ≠ Indian reality** (dengue, TB, resource constraints)

## Solution

Clinical-Mind is a multi-layered reasoning development platform:

1. **RAG-Powered Case Generation** - Dynamic cases from Indian medical literature
2. **Socratic AI Tutor** - Multi-turn dialogue that asks "why" until deep understanding
3. **Cognitive Bias Detection** - Tracks patterns across 20+ cases, identifies biases
4. **Knowledge Graph Visualization** - Interactive D3.js map of concept mastery
5. **Performance Analytics** - Personalized dashboard with peer benchmarking
6. **India-Centric Content** - Cases set in Indian hospitals with regional disease patterns

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS |
| Visualization | D3.js (knowledge graph), Recharts (analytics) |
| Backend | Python 3.11+, FastAPI |
| AI Engine | Claude Opus 4.6 (Anthropic API) |
| Vector DB | ChromaDB + LangChain |
| Embeddings | Sentence-Transformers |

## Quick Start

### Frontend
```bash
cd frontend
npm install
npm start
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Environment Variables
```bash
cp backend/.env.example backend/.env
# Add your ANTHROPIC_API_KEY
```

## Project Structure

```
clinical-mind/
├── frontend/                  # React + TypeScript UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/            # Design system (Button, Card, Badge, etc.)
│   │   │   ├── layout/        # Header, Footer, Layout
│   │   │   ├── case/          # Case-specific components
│   │   │   └── visualizations/ # D3.js, Recharts components
│   │   ├── pages/
│   │   │   ├── Landing.tsx     # Home page
│   │   │   ├── CaseBrowser.tsx # Browse/filter cases
│   │   │   ├── CaseInterface.tsx # Main case-solving experience
│   │   │   ├── Dashboard.tsx   # Performance analytics
│   │   │   └── KnowledgeGraph.tsx # D3.js knowledge map
│   │   ├── types/             # TypeScript interfaces
│   │   └── hooks/             # Custom React hooks
│   └── public/
├── backend/                   # FastAPI + Python
│   ├── app/
│   │   ├── api/               # REST endpoints
│   │   ├── core/
│   │   │   ├── rag/           # RAG case generation
│   │   │   ├── agents/        # Socratic tutor AI
│   │   │   └── analytics/     # Bias detection, knowledge graph
│   │   └── models/            # Data models
│   └── data/
│       └── medical_corpus/    # Medical literature for RAG
└── docs/                      # Documentation
```

## Key Features

### Interactive Case Interface
- Progressive information reveal (history → exam → labs)
- Real-time AI tutor sidebar with Socratic questioning
- Diagnosis submission with detailed feedback

### Cognitive Bias Detection
- Tracks anchoring, premature closure, availability, and confirmation biases
- Statistical analysis across case history
- Personalized recommendations to counter biases

### Knowledge Graph
- Interactive D3.js force-directed graph
- Color-coded by category (specialty, diagnosis, symptom, investigation)
- Shows strong vs weak concept connections
- Click nodes to see mastery details

### Performance Dashboard
- Accuracy trends over time (area charts)
- Specialty-wise performance breakdown
- Bias radar chart
- Personalized case recommendations

## Design Philosophy

Inspired by Honest Greens + Linear:
- **Warm, organic palette** (cream backgrounds, forest greens, terracotta accents)
- **Larger typography** (18px body minimum for long study sessions)
- **Generous spacing** and smooth transitions (400ms ease-out)
- **Premium but approachable** - professional without being intimidating

## Hackathon

Built for **Problem Statement #3: "Amplify Human Judgment"**
- AI sharpens medical expertise without replacing it
- Makes students dramatically more capable
- Keeps humans in the loop

## License

MIT
