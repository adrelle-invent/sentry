import time
import uuid

import structlog
from config import settings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from core.rate_limiter import limiter


def register_middlewares(app: FastAPI) -> None:
    """Register all global application middlewares, CORS, telemetry, and rate limiting hooks."""

    # 1. Custom Request ID & Execution Time Telemetry Middleware
    @app.middleware("http")
    async def add_request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            return response
        finally:
            # CRITICAL: Always unbind/clear request-specific context in a finally block
            # so it never leaks into pooled async worker tasks.
            structlog.contextvars.unbind_contextvars("request_id")

    # 2. Rate Limiter State & Exception Handling (SlowAPI)
    app.state.limiter = limiter
    app.add_exception_handler(
        RateLimitExceeded,
        _rate_limit_exceeded_handler,  # type: ignore
    )
    app.add_middleware(SlowAPIMiddleware)

    # 3. CORS Middleware Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
