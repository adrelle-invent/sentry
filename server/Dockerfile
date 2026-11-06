# ==========================================
# Stage 1: Build dependencies and virtual environment
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS builder

WORKDIR /app

# Optimize uv settings for container builds
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies first (leveraging Docker cache layers)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# Copy application source code and install the project itself
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ==========================================
# Stage 2: Minimal production runtime image
# ==========================================
FROM python:3.12-slim-trixie

WORKDIR /app

# Runtime environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Copy only the pre-built virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the application code
COPY . .

# Run the app
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "3001"]