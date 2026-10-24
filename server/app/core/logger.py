import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """Configure global logging, swapping between colored console logs and JSON."""
    
    # Check if we are running in production
    is_production = getattr(settings, "ENVIRONMENT", "development").lower() == "production"

    # Shared processors used by both structlog and standard library loggers
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Pick the appropriate renderer based on environment
    if is_production:
        # Production: Strict, single-line JSON strings for log aggregators (Datadog, ELK)
        final_renderer = structlog.processors.JSONRenderer()
        log_level = logging.INFO
    else:
        # Development: Gorgeous, human-readable, color-coded terminal text
        final_renderer = structlog.dev.ConsoleRenderer(colors=True)
        log_level = logging.DEBUG

    # Configure structlog behavior
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set up standard library logging handler with the dynamic renderer
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            final_renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Intercept uvicorn and fastapi logs so they use the same formatting
    for logger_name in ("uvicorn", "uvicorn.access", "fastapi"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False


def get_logger(name: str):
    """Factory function to get a bound structured logger for a module."""
    return structlog.get_logger(name)