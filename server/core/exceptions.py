from fastapi import FastAPI, Request
from fastapi.exceptions import StarletteHTTPException
from fastapi.responses import JSONResponse

from core.logger import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base application error conforming to the strict response envelope."""

    def __init__(
        self,
        message: str | list[str],
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
    ):
        self.messages = [message] if isinstance(message, str) else message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.messages[0] if self.messages else "")


class NotFoundError(AppError):
    def __init__(
        self, message: str = "Requested resource not found", error_code: str = "NOT_FOUND"
    ):
        super().__init__(message=message, status_code=404, error_code=error_code)


class UnauthorizedError(AppError):
    def __init__(
        self, message: str = "Could not validate credentials", error_code: str = "UNAUTHORIZED"
    ):
        super().__init__(message=message, status_code=401, error_code=error_code)


def register_exception_handlers(app: FastAPI) -> None:
    """Registers global exception handlers enforcing the clean response format."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning(
            "app_error_raised",
            path=request.url.path,
            error_code=exc.error_code,
            status_code=exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "data": None,
                "errors": [{"code": exc.error_code, "message": msg} for msg in exc.messages],
                "message": exc.messages[0] if exc.messages else None,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "data": None,
                "errors": [{"code": "HTTP_ERROR", "message": exc.detail}],
                "message": str(exc.detail),
                "status_code": exc.status_code,
            },
        )