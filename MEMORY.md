# Clinical-Mind - Development Memory

## Key Decisions

### Design
- **Color Palette:** Warm, organic (Honest Greens inspired)
  - Primary: Forest green (#2D5C3F), not generic blue
  - Backgrounds: Cream (#FFFCF7), warm grays
  - Accents: Terracotta (#C85835), sage green (#6B8E6F)

- **Typography:** Larger than typical (18px body)
  - Font: Inter (clean, professional)
  - Generous line heights (1.6-1.8)

- **Visualizations:** Code-based (D3.js, Recharts)
  - No image generation APIs needed
  - Interactive, data-driven

### Architecture
- **Frontend:** React 18 + TypeScript + Tailwind CSS v4
- **Backend:** FastAPI + Python
- **AI:** Claude Opus 4.6 (Socratic dialogue)
- **Database:** ChromaDB (vector store for RAG)
- **Charts:** Recharts v3 (with type workarounds for React 18)

### Technical Notes
- Recharts v3 has type incompatibilities with React 18 TypeScript
  - Solution: Cast components to `any` for JSX compatibility
- Tailwind CSS v4 uses `@theme` directive instead of `tailwind.config.js`
- D3.js v7 works well with React useRef/useEffect pattern

## What's Working
- Frontend builds successfully (React + TypeScript + Tailwind v4)
- All 5 pages implemented (Landing, CaseBrowser, CaseInterface, Dashboard, KnowledgeGraph)
- UI component library (Button, Card, Badge, Input, StatCard)
- Layout components (Header, Footer, Layout with routing)
- Backend API structure (FastAPI with cases, student, analytics endpoints)
- Sample medical cases (Cardiology, Infectious, Neurology)
- Bias detection engine (anchoring, premature closure, availability, confirmation)
- Knowledge graph builder with demo data
- D3.js force-directed graph visualization
- Recharts analytics (area chart, radar chart)

## Architecture Decisions
- Demo data is hardcoded for hackathon speed
- Socratic tutor uses keyword matching (can be upgraded to Claude API)
- Case generator returns pre-built cases (can be upgraded to RAG + Claude)
- In-memory storage (no persistent database for demo)
