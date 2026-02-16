FROM python:3.10-slim

# Install Node.js for building React frontend
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend files
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy and build frontend
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# Copy backend code
WORKDIR /app
COPY backend/ ./backend/

# Create a simple server script to serve both frontend and backend
RUN echo '#!/usr/bin/env python3\n\
import os\n\
import sys\n\
sys.path.insert(0, "/app/backend")\n\
from fastapi import FastAPI\n\
from fastapi.staticfiles import StaticFiles\n\
from fastapi.responses import FileResponse\n\
from app.main import app\n\
\n\
# Mount the React build as static files\n\
app.mount("/static", StaticFiles(directory="/app/frontend/build/static"), name="static")\n\
\n\
# Serve the React app for all non-API routes\n\
@app.get("/{full_path:path}")\n\
async def serve_spa(full_path: str):\n\
    if full_path.startswith("api/"):\n\
        return {"error": "Not found"}\n\
    index_path = "/app/frontend/build/index.html"\n\
    if os.path.exists(index_path):\n\
        return FileResponse(index_path)\n\
    return {"error": "Frontend not found"}\n\
\n\
if __name__ == "__main__":\n\
    import uvicorn\n\
    port = int(os.environ.get("PORT", 7860))\n\
    uvicorn.run(app, host="0.0.0.0", port=port)\n\
' > /app/serve.py

RUN chmod +x /app/serve.py

# Expose the port that Hugging Face Spaces expects
EXPOSE 7860

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV NODE_ENV=production

# Run the combined server
CMD ["python", "/app/serve.py"]