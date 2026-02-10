# Multi-stage build for LLM Deployment Platform

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY frontend/src ./src
COPY frontend/index.html ./
COPY frontend/vite.config.ts ./
COPY frontend/tsconfig.json ./

# Build frontend
RUN npm run build

# Stage 2: Build backend and combine with frontend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY app/requirements.txt ./app/

# Install Python dependencies
RUN pip install --no-cache-dir -r ./app/requirements.txt

# Copy backend code
COPY app ./app

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy .env.example as .env template (user should override)
COPY .env.example .env.example 2>/dev/null || true

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start backend server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
