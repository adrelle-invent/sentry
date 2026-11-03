from app.core.exceptions import AppError


class EventNotFoundError(AppError):
    status_code = 404
