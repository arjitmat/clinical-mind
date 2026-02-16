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

# Copy backend code and root app.py
WORKDIR /app
COPY backend/ ./backend/
COPY app.py ./

# Expose the port that Hugging Face Spaces expects
EXPOSE 7860

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV NODE_ENV=production

# Run the combined server using app.py (proper SPA + API routing)
CMD ["python", "app.py"]
