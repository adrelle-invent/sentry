from app.core.exceptions import AppError


class LogNotFoundError(AppError):
    status_code = 404
