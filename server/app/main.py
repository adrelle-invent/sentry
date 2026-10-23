from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.logs.router import router as logs_router

# from app.issues.router import router as issues_router
from app.shared.cache import redis
from app.shared.logger import configure_logging, get_logger
from app.shared.rate_limiter import limiter

configure_logging()

logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="AD. Sentry")

    app.state.limiter = limiter
    app.add_exception_handler(
        RateLimitExceeded,
        _rate_limit_exceeded_handler,  # type: ignore
    )
    app.add_middleware(SlowAPIMiddleware)

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
    @limiter.exempt
    async def health(request: Request):
        return {"status": "ok"}

    @app.get("/clear-redis")
    async def clear_redis():
        try:
            await redis.flushdb()
            logger.info("Redis cleared")
            return {"status": "cleared"}
        except Exception as e:
            logger.exception("Error clearing Redis")
            return {"status": "error", "message": str(e)}

    return app


app: FastAPI = create_app()
