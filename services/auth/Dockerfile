# Multi-stage build for Auth service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Development stage
FROM base as development

WORKDIR /app

# Copy poetry files
COPY pyproject.toml ./

# Install dependencies (generate lock file if needed)
RUN poetry lock --no-update && poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY . .

# Install the package in development mode
RUN poetry lock --no-update && poetry install

EXPOSE 8010

# Default command for development (overridden in docker-compose)
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010", "--reload"]

# Production stage
FROM base as production

WORKDIR /app

# Copy poetry files
COPY pyproject.toml ./

# Install only production dependencies
RUN poetry lock --no-update && poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Create non-root user
RUN adduser --disabled-password --gecos '' --shell /bin/bash user \
    && chown -R user:user /app
USER user

# Copy application code
COPY --chown=user:user . .

# Install the package
RUN poetry install --only=main

EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

# Production command
CMD ["poetry", "run", "gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8010"]