# ==============================================================================
# Dockerfile for GlooHack FastAPI Backend Services
# Multi-stage build for optimized image size and enhanced security
# ==============================================================================

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system build dependencies required for compiling C extensions (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies into temporary directory
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# Stage 2: Runtime environment
FROM python:3.11-slim AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    ENVIRONMENT=production

WORKDIR /app

# Install runtime dependencies (libpq for postgres driver, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY app /app/app
COPY README.md /app/README.md

# Set non-root permissions
RUN chown -R appuser:appuser /app
USER appuser

# Expose backend port
EXPOSE 8000

# Container health check via FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch production server via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
