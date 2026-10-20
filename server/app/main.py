from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.logs.router import router as logs_router

# from app.issues.router import router as issues_router
from app.shared.cache import redis


def create_app() -> FastAPI:
    app = FastAPI(title="AD. Sentry")

    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

    # Add CORS Middleware to support frontend requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(logs_router)
    # app.include_router(issues_router)

    @app.get("/healthz")
    async def health():
        return {"status": "ok"}

    @app.get("/clear-redis")
    async def clear_redis():
        try:
            await redis.flushdb()
            return {"status": "cleared"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return app


app: FastAPI = create_app()
