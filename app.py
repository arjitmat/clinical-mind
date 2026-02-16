#!/usr/bin/env python3
"""
Clinical Mind - Hugging Face Spaces Deployment
Combined FastAPI backend + React frontend server
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Set environment variables for Hugging Face Spaces
os.environ["HF_SPACE"] = "1"

# Disable ChromaDB telemetry to avoid posthog capture() errors
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the main FastAPI app from backend
from app.main import app

# Update CORS for Hugging Face Spaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:7860",
        "https://huggingface.co",
        "https://arjitmat-clinical-mind.hf.space",
        "*"  # Allow all origins in HF Spaces
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check if frontend build exists
frontend_build_path = Path(__file__).parent / "frontend" / "build"
if frontend_build_path.exists():
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")

    # Serve the React app for all non-API routes
    @app.get("/", response_class=HTMLResponse)
    @app.get("/demo", response_class=HTMLResponse)
    @app.get("/cases", response_class=HTMLResponse)
    @app.get("/case/{path:path}", response_class=HTMLResponse)
    @app.get("/dashboard", response_class=HTMLResponse)
    @app.get("/profile", response_class=HTMLResponse)
    @app.get("/knowledge-graph", response_class=HTMLResponse)
    @app.get("/adversarial", response_class=HTMLResponse)
    @app.get("/reasoning", response_class=HTMLResponse)
    async def serve_spa(path: str = None):
        """Serve the React single-page application"""
        index_file = frontend_build_path / "index.html"
        if index_file.exists():
            with open(index_file) as f:
                content = f.read()
                # Update API URL for Hugging Face Spaces
                if "HF_SPACE" in os.environ:
                    content = content.replace(
                        "http://localhost:8000/api",
                        "/api"
                    )
                return HTMLResponse(content=content)
        return HTMLResponse(content="<h1>Frontend not found. Building...</h1>")
else:
    @app.get("/", response_class=HTMLResponse)
    async def no_frontend():
        return HTMLResponse(content="""
        <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>🏥 Clinical Mind</h1>
                <p>Frontend is building... Please wait a moment and refresh.</p>
                <p>Visit <a href="/docs">/docs</a> for API documentation.</p>
            </body>
        </html>
        """)

if __name__ == "__main__":
    # Get port from environment or use Hugging Face default
    port = int(os.environ.get("PORT", 7860))

    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )