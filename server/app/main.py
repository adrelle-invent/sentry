from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.logs.router import router as logs_router

# from app.issues.router import router as issues_router
from app.shared.cache import cache
from app.shared.logger import configure_logging, get_logger
from app.shared.rate_limiter import limiter

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.ping()
    yield  # Application runs and serves traffic here
    await cache.close()


def create_app() -> FastAPI:
    app = FastAPI(title="AD. Sentry", lifespan=lifespan)

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
        """Clear Redis cache using the injected cache driver."""
        if await cache.clear():
            return {"status": "cleared"}

        return {
            "status": "error",
            "message": "Failed to clear cache. Check server logs.",
        }

    return app


app: FastAPI = create_app()
