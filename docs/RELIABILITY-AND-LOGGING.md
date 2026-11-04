# Reliability, Logging & Error Handling

This document establishes the standards for telemetry, structured logging (`structlog`), request tracing, and global error handling across the backend services of the **ADrelle** platform.

---

## 1. Structured Logging with `structlog`

To ensure production logs are machine-readable, indexable, and rich with context, all backend services use `structlog` configured for JSON output in production and human-readable console formatting during local development.

### Configuration Standards

* **Context Binding:** Use context variables to automatically inject request-scoped metadata (such as `request_id`, `user_id`, and `client_ip`) into every log entry.
* **Log Levels:**
* `DEBUG`: Detailed diagnostic information for local troubleshooting.
* `INFO`: Normal operational events (e.g., server startup, background task completion).
* `WARNING`: Non-critical anomalies that do not disrupt service execution.
* `ERROR`: Failures requiring immediate attention or alerting.



---

## 2. Request Tracing & Correlation IDs

Every incoming HTTP request is assigned a unique tracking identifier to enable end-to-end telemetry across database queries, application logs, and external API calls.

### Middleware Implementation

1. **Correlation ID Generation:** A custom middleware checks incoming headers for `X-Request-ID`. If absent, it generates a new UUIDv4 correlation ID.
2. **Context Var Propagation:** The ID is stored in a Python `contextvars.ContextVar`, making it globally accessible to any function or database session within the request lifecycle without explicit parameter passing.
3. **Response Header:** The correlation ID is reflected back to the client in the `X-Request-ID` response header for client-side debugging.

---

## 3. Global Error Handling & Domain Exceptions

To prevent unhandled exceptions from leaking stack traces or returning inconsistent error structures, all errors are caught by global exception handlers in FastAPI (`server/main.py`).

### Standardized Error Envelope

Every error response returned by the API follows a strict JSON structure:

```json
{
  "error": {
    "code": "DOMAIN_ERROR_CODE",
    "message": "Human-readable description of the error.",
    "details": {}
  },
  "request_id": "uuid-v4-correlation-id"
}

```

### Domain Exceptions (`exceptions.py`)

Business modules must define custom exceptions inheriting from a base `DomainError` class. These exceptions map cleanly to specific HTTP status codes (e.g., `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`), keeping routers clean and business logic testable.

---

## 4. Health Checks & Reliability Probes

To integrate smoothly with container orchestrators and monitoring tools, the application provides standardized health check endpoints:

* **Liveness Probe (`/health/live`):** Verifies that the FastAPI application process is running and responsive.
* **Readiness Probe (`/health/ready`):** Validates external dependencies, including active connectivity to the PostgreSQL database and Redis cache.

---