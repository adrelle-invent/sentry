# API Contract & Type Synchronization

This document establishes the specifications for backend-to-frontend communication, OpenAPI schema generation, and automated TypeScript type synchronization for the **AD. Sentry** platform.

---

## 1. Core Principle: Single Source of Truth

To maintain strict type safety across the stack without the overhead of a separate monorepo workspace package, the backend's runtime **OpenAPI schema** serves as the single source of truth for all API contracts.

- The **FastAPI backend** automatically generates the JSON schema at `/openapi.json`.
- The **React client** consumes these generated types to guarantee compile-time safety for all request payloads and response bodies.

---

## 2. Backend OpenAPI Configuration

FastAPI natively generates OpenAPI 3.0 documentation. To ensure predictable type generation for the client, all endpoints must adhere to strict typing rules:

- **Pydantic Schemas:** Every request body and response must use explicit Pydantic models defined in `server/modules/<domain>/schemas.py`. Never return raw dictionaries or primitive types from routers.
- **Explicit Status Codes:** All routing decorators must declare explicit status codes (e.g., `@router.post("/items", status_code=status.HTTP_201_CREATED)`).
- **Standardized Errors:** Error responses must adhere to the global error envelope defined in the core architecture.

---

## 3. Client-Side Type Synchronization Workflow

To bridge the backend schemas with the TypeScript client, AD. Sentry utilizes an automated generation pipeline.

### Step 1: Exporting the Schema

When the backend server is running, the OpenAPI JSON schema can be exported directly:

```bash
curl http://localhost:8000/openapi.json > client/src/api/openapi.json
```

### Step 2: Generating TypeScript Definitions

Using a schema-to-types code generator (such as `openapi-typescript`), the raw JSON schema is compiled into clean TypeScript interfaces:

```bash
pnpm --filter client generate-api
```

This command outputs the types directly into `client/src/api/api.ts`.

---

## 4. API Client Integration Pattern

The frontend interacts with the backend through a centralized, typed HTTP client wrapper located at `client/src/api/client.ts`.

- **Base Configuration:** Configures base URLs, interceptors for injecting JWT authorization headers, and global error handling for expired sessions or network failures.
- **Typed Requests:** Consumes the generated definitions from `client/src/api/api.ts` to ensure request parameters and response hooks are fully typed.
