# 🔥 Elite Multi-Agent Collaborative Coding System - Production Docker Image
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    nodejs \
    npm \
    sqlite3 \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -g 1000 elitecrew && \
    useradd -r -u 1000 -g elitecrew elitecrew

# Set work directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
COPY requirements-prod.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/templates /app/static && \
    chown -R elitecrew:elitecrew /app

# Switch to non-root user
USER elitecrew

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/system/status || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "web_dashboard:app", "--host", "0.0.0.0", "--port", "8000"]

# Production stage
FROM base as production

# Install production-only dependencies
RUN pip install --no-cache-dir gunicorn uvicorn[standard]

# Production command
CMD ["gunicorn", "web_dashboard:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

# Development stage
FROM base as development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Development command
CMD ["python", "-m", "uvicorn", "web_dashboard:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]