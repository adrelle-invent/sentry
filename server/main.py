from fastapi import FastAPI, Request

from core.config import settings
from core.exceptions import register_exception_handlers
from core.lifespan import lifespan
from core.logger import configure_logging, get_logger
from core.middleware import register_middlewares
from core.rate_limiter import limiter
from modules.telemetry.router import router as events_router

configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME, lifespan=lifespan, debug=settings.APP_DEBUG
    )

    register_exception_handlers(app)
    register_middlewares(app)
    _register_routes(app)

    return app


def _register_routes(app: FastAPI) -> None:
    app.include_router(events_router, prefix="/api/v1", tags=["events"])

    @app.get("/healthz")
    @limiter.exempt
    async def health(request: Request):
        return {"status": "healthy"}


app: FastAPI = create_app()
