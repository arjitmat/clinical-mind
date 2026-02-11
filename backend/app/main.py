from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import cases, student, analytics

app = FastAPI(
    title="Clinical-Mind API",
    description="AI-powered clinical reasoning simulator for medical students",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router, prefix="/api/cases", tags=["cases"])
app.include_router(student.router, prefix="/api/student", tags=["student"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/")
async def root():
    return {"message": "Clinical-Mind API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
