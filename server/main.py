from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from core.exceptions import AppError
from core.lifespan import lifespan
from core.logger import configure_logging, get_logger
from core.rate_limiter import limiter
from modules.telemetry.router import router as events_router

# from modules.issues.router import router as issues_router

configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="AD. Sentry", lifespan=lifespan)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled server error: %s", exc)
        return JSONResponse(status_code=500, content="Internal Server Error")

    @app.exception_handler(AppError)
    async def app_exception_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

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

    app.include_router(events_router)
    # app.include_router(issues_router)

    @app.get("/healthz")
    @limiter.exempt
    async def health(request: Request):
        return {"status": "ok"}

    return app


app: FastAPI = create_app()
