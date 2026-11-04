# 👁️ AD. Sentry — Infrastructure & System Observability

> Internal monitoring and compliance engine tracking system telemetry, performance metrics, and audit logs.

- Distributed APM tracing, server telemetry, and health metrics
- Cryptographic tamper-evident audit logging for SOC 2 compliance
- Real-time SLA threshold monitoring and system alert routing

> Engineered for reliability. Designed for scale. Built to evolve.

---

## 📁 Repository Structure

```text
repo/
├── .agents/                        # AI agent configurations and context
├── docs/                           # System architecture, runbooks, and API specs
├── client/                         # React + Vite frontend application
│   ├── src/
│   │   ├── api/                    # API client and generated TypeScript types
│   │   ├── components/             # Global shared UI atoms
│   │   ├── modules/                # Domain-specific frontend slices (e.g., auth/)
│   │   └── router.tsx              # Application routing
│   └── package.json
├── server/                         # FastAPI backend service
│   ├── alembic/                    # Database migrations
│   ├── core/                       # Global configuration, database, and security
│   ├── modules/                    # Vertical domain slices (router, services, models, schemas)
│   └── pyproject.toml
├── infra/                          # Docker Compose and local reverse proxy (Nginx)
├── Makefile                        # Unified command runner
└── README.md

```

---

## 🚀 Quickstart Guide

The root `Makefile` orchestrates your local development workflow across Docker Compose, migrations, dependencies, and servers.

### 1. Prerequisites

- Docker & Docker Compose
- Python 3.12+ & `uv`
- Node.js 24+ & `pnpm`
- Make

### 2. Start Infrastructure

Spin up PostgreSQL and Redis backing services:

```bash
make infra-up

```

### 3. Setup and Run Backend

```bash
cd server
cp .env.example .env
# Edit .env with your local database credentials
uv sync --locked
alembic upgrade head

```

Run the FastAPI development server:

```bash
make server-dev

```

### 4. Setup and Run Frontend

In a separate terminal:

```bash
cd client
pnpm install
make client-dev

```

---

## 📚 Documentation Directory

Comprehensive technical blueprints and operational runbooks are maintained in the `docs/` folder:

- [Architecture Overview](docs/ARCHITECTURE.md) — System topology, domain-driven structure, and execution lifecycles.
- [Development Guide](docs/DEVELOPMENT.md) — Local environment setup, toolchain requirements, and debugging guidelines.
- [API Contract & Types](docs/API-CONTRACT.md) — OpenAPI generation and frontend-to-backend type synchronization workflow.
- [Database Schema](docs/DATABASE-SCHEMA.md) — Asynchronous SQLAlchemy models, Alembic standards, and indexing strategies.
- [Reliability & Logging](docs/RELIABILITY-AND-LOGGING.md) — Structlog configuration, correlation ID tracing, and global error handling.
- [Deployment Runbook](docs/DEPLOYMENT-RUNBOOK.md) — Multi-stage container builds, CI/CD pipelines, and zero-downtime release steps.
