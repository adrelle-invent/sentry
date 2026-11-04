# Development Guide

Welcome to the development guide for **AD. Sentry**. This document outlines the toolchain setup, local environment configuration, running services via Docker Compose, and executing tests.

---

## 1. Prerequisites & Toolchain

Before getting started, ensure you have the following installed on your development machine (Linux, WSL Ubuntu, or macOS):

- **Docker & Docker Compose:** For running containerized backing services (PostgreSQL, Redis).
- **Python 3.12+ & `uv`:** Recommended modern Python dependency and package manager.
- **Node.js 24+ & `pnpm`:** Fast, deterministic Node.js package manager for the React client.
- **Make:** For orchestrating unified root commands.

---

## 2. Environment Variables Setup

You need to configure your local environment variables before booting the application.

1. Copy the example environment file in the `server/` directory:

```bash
cp server/.env.example server/.env
```

2. Update the database URL and security secrets inside `server/.env` to match your local setup.

---

## 3. Running Locally with Docker Compose

The fastest way to spin up the entire supporting infrastructure (database, cache, and optional proxy) is via Docker Compose inside the `infra/` folder.

1. Start backing services:

```bash
make up # docker compose -f infra/docker-compose.yml up -d
```

2. Verify containers are healthy:

```bash
make ps # docker compose -f infra/docker-compose.yml ps
```

---

## 4. Backend Development (`server/`)

To run the FastAPI backend locally with hot-reloading:

1. Navigate to the server directory and set up your virtual environment using `uv`:

```bash
cd server
uv run sync --locked
```

2. Run database migrations via Alembic:

```bash
alembic upgrade head
```

3. Start the FastAPI development server:

```bash
make fastapi # uv run fastapi dev
```

The interactive API docs will be available at `http://localhost:8000/docs`.

---

## 5. Frontend Development (`client/`)

To run the React + Vite client locally:

1. Navigate to the client directory and install dependencies:

```bash
cd client
pnpm install
```

2. Start the Vite development server:

```bash
pnpm dev
```

The client will run at `http://localhost:5173`.

---

## 6. Running Tests

### Backend Tests

The backend test suite uses `pytest` and mirrors the `server/modules/` layout. Run tests with:

```bash
cd server
uv run pytest
```

### Frontend Tests

Run unit tests for components and hooks using:

```bash
cd client
pnpm test
```

### Repository Structure

```
repo/
├── .agents/                        # AI agent context configurations and custom scripts
├── docs/                           # Version-controlled system documentation & runbooks
│   ├── ARCHITECTURE.md             # System components, topology, and core data flow
│   ├── DEVELOPMENT.md              # Local setup, Docker environment, toolchain, & running tests
│   ├── API-CONTRACT.md             # API endpoints, request/response schemas, & error formats
│   ├── DATABASE-SCHEMA.md          # ERD, migrations, indexing strategies, & table definitions
│   ├── RELIABILITY-AND-LOGGING.md  # Structlog standards, error handling, retries, & health checks
│   └── DEPLOYMENT-RUNBOOK.md       # CI/CD pipelines, environment variables, & release steps
├── client/                         # React + Vite frontend application
│   ├── src/
│   │   ├── api/                    # Centralized API client & generated OpenAPI types
│   │   │   ├── client.ts           # Configured HTTP wrapper (fetch/axios)
│   │   │   └── api.ts              # Automatically generated TypeScript types from FastAPI schema
│   │   ├── components/             # Global, shared UI design atoms (Button, Modal, Input)
│   │   ├── modules/                # Domain-specific frontend vertical slices
│   │   │   └── auth/               # e.g., Auth module (LoginForm, useAuth, auth components)
│   │   │       ├── components/     # Module-specific UI components
│   │   │       └── hooks/          # Module-specific state and query hooks
│   │   ├── hooks/                  # Global shared hooks (useLocalStorage, useDebounce)
│   │   ├── pages/                  # Route-level view components (DashboardPage.tsx)
│   │   ├── router.tsx              # React Router declarative route mapping
│   │   └── main.tsx                # Vite application entry point
│   ├── package.json                # Frontend dependencies and npm scripts
│   └── Dockerfile                  # Multi-stage production build for the web client
├── server/                         # FastAPI backend service
│   ├── alembic/                    # Database migration scripts and environment setup
│   ├── core/                       # Global cross-cutting concerns (config, DB engine, security)
│   │   ├── config.py               # Pydantic-settings strict environment variable validation
│   │   ├── database.py             # SQLAlchemy async session maker and dependency injection
│   │   └── security.py             # Password hashing and token utilities
│   ├── modules/                    # Vertical feature domain slices (business logic)
│   │   └── auth/                   # e.g., Auth domain module
│   │       ├── router.py           # FastAPI HTTP routing endpoints
│   │       ├── services.py         # Pure business logic and domain execution
│   │       ├── models.py           # SQLAlchemy ORM table definitions
│   │       ├── schemas.py          # Pydantic validation schemas for request/response
│   │       ├── exceptions.py       # Domain-specific custom errors
│   │       └── worker/             # Background tasks and asynchronous processing for auth
│   ├── tests/                      # Pytest test suite mirroring backend structure
│   ├── main.py                     # FastAPI application factory, middleware, and router mounting
│   ├── Dockerfile                  # Production container configuration for FastAPI
│   └── pyproject.toml              # Python dependency management (managed by uv / poetry)
├── infra/                          # Infrastructure and orchestration configuration
│   ├── nginx/                      # Reverse proxy and SSL termination configs
│   └── docker-compose.yml          # Local multi-container development environment (DB, API, Client)
├── Makefile                        # Unified command runner for dev, build, migrate, and test workflows
└── README.md                       # High-level project overview and quickstart guide
```
