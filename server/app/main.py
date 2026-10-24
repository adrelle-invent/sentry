from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.lifespan import lifespan
from app.core.logger import configure_logging, get_logger
from app.core.rate_limiter import limiter
from app.modules.logs.router import router as logs_router

# from app.modules.issues.router import router as issues_router

configure_logging()
logger = get_logger(__name__)


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

    return app


app: FastAPI = create_app()
