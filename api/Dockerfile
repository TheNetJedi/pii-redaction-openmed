# RedactX API Dockerfile
# Production-ready container for PII redaction service
# Build context must be project root

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python build tools
RUN pip install --no-cache-dir --upgrade pip build hatchling

# 1. Install Core Library
COPY core /tmp/core
RUN pip install --no-cache-dir /tmp/core

# 2. Install API Dependencies
COPY api/requirements.txt /tmp/api/requirements.txt
RUN pip install --no-cache-dir -r /tmp/api/requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash redactx

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code preserving structure
COPY --chown=redactx:redactx core /app/core
COPY --chown=redactx:redactx api /app/api

# Create model cache directory
RUN mkdir -p /tmp/redactx/models && chown -R redactx:redactx /tmp/redactx

# Switch to non-root user
USER redactx
WORKDIR /app/api

# Environment variables
ENV REDACTX_HOST=0.0.0.0
ENV REDACTX_PORT=8000
ENV REDACTX_MODEL_CACHE_DIR=/tmp/redactx/models
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure core is accessible
ENV PYTHONPATH="/app/core:${PYTHONPATH}"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
