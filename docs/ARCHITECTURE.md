# System Architecture & Technical Design (`docs/ARCHITECTURE.md`)

This document details the high-level architecture, system topology, component interactions, and data flow for the **AD. Sentry** platform.

---

## 1. High-Level System Overview

AD. Sentry is structured as a unified monorepo containing a decoupled **React + Vite** frontend (`client/`) and a high-performance **FastAPI** backend (`server/`). The application follows a **vertical-slice, domain-driven design (DDD)**, encapsulating business logic inside self-contained modules rather than traditional technical layers.

```
[ Web Browser Client ]
          │
          │ HTTP / JSON API
          ▼
   [ Nginx Proxy ] (SSL Termination & Routing)
          │
          ├── / ───────► [ React + Vite Client (Static / SPA) ]
          └── /api/ ───► [ FastAPI Backend Service ]
                               │
                               ├── Async Sessions ──► [ PostgreSQL Database ]
                               └── Background Tasks ─► [ Redis / Async Worker ]

```

---

## 2. Core Components & Topology

### 2.1 Web Client (`client/`)

* **Framework:** React with Vite build toolchain.
* **Architecture:** Modular, feature-first structure (`src/modules/`).
* **State & API Integration:** Centralized API client (`src/api/client.ts`) utilizing automatically generated OpenAPI TypeScript definitions (`src/api/api.ts`) directly from the backend schema.
* **Styling & UI:** Atomic shared components (`src/components/`) combined with module-specific UI elements.

### 2.2 Backend API (`server/`)

* **Framework:** FastAPI (Python) running on an asynchronous ASGI server (Uvicorn).
* **Architecture:** Vertical-slice domain modules (`server/modules/<domain>/`).
* **Database & ORM:** SQLAlchemy (AsyncIO engine) with Alembic migration engine (`server/alembic/`).
* **Configuration:** Strict environment variable validation at startup via Pydantic (`server/core/config.py`).
* **Task Processing:** Embedded or decoupled worker layer (`server/modules/<domain>/worker/`) for handling asynchronous background processing.

### 2.3 Infrastructure & Proxy (`infra/`)

* **Orchestration:** Docker Compose (`infra/docker-compose.yml`) for local multi-container development.
* **Gateway / Proxy:** Nginx for unified request routing, CORS configuration, and local SSL handling.

---

## 3. Data Flow & Execution Lifecycles

### 3.1 Request Execution Lifecycle

```
[ Request ] ──► FastAPI Router (router.py)
                     │
                     ├─ Validation (schemas.py)
                     │
                     ▼
              Service Layer (services.py) ──► ORM (models.py) ──► Database
                     │
                     ├─ Error Handler (exceptions.py)
                     │
                     ▼
             Response Contract (schemas.py) ──► [ JSON Response ]

```

1. **Transport Layer (`router.py`):** Receives incoming HTTP requests, handles query/path params, validates request payloads via **Pydantic Schemas** (`schemas.py`), and injects core dependencies (e.g., database session `get_db`).
2. **Domain Service Layer (`services.py`):** Encapsulates pure business logic. Decoupled completely from HTTP transport mechanics. Manages database transactions via SQLAlchemy.
3. **Data Boundary (`models.py`):** Maps domain state to the relational PostgreSQL database schema.
4. **Error Handling (`exceptions.py`):** Triggers domain-specific exceptions, which are transformed by central FastAPI middleware into standardized JSON error responses.

### 3.2 End-to-End Type Safety Workflow

To ensure seamless alignment between frontend consumption and backend contracts:

1. FastAPI automatically exposes an updated OpenAPI schema definition at runtime.
2. The code generator outputs strict TypeScript type definitions directly into `client/src/api/api.ts`.
3. React components and hooks consume typed endpoints directly from `client/src/api/client.ts`.

---

## 4. Operational & Design Invariants

* **Module Autonomy:** Modules in `server/modules/` and `client/src/modules/` must remain self-contained. Inter-module interactions should occur via public service interfaces rather than accessing private internal utilities.
* **Progressive Extraction:** New features should start simple inside `router.py` and `models.py`. Separate `services.py`, `exceptions.py`, and `worker/` sub-files only when complexity demands it.
* **Explicit DB Transactions:** Database sessions yield transaction boundaries to `services.py`. Automatic implicit commits in routers are strictly prohibited.