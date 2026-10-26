# ==========================================
# Stage 1: Build Frontend Single Page App
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Production Python & Flask Runtime
# ==========================================
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download lightweight spacy model (fallback to blank if network restricted)
RUN python -m spacy download en_core_web_sm || true

# Copy backend, sample documents, scripts, and root runner
COPY backend /app/backend
COPY sample_documents /app/sample_documents
COPY scripts /app/scripts
COPY run.py /app/run.py

# Copy pre-compiled frontend distribution from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Set Python Path and Environment
ENV PYTHONPATH=/app
ENV PORT=5000
ENV FLASK_ENV=production

# Create required directories
RUN mkdir -p /app/backend/instance /app/backend/uploads /app/backend/exports

# Pre-seed initial sample documents into SQLite database
RUN python scripts/seed_demo_data.py || true

EXPOSE 5000

# Start production WSGI server
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "backend.app:create_app()"]
