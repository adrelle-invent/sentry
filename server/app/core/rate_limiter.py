from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Initialize the limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    default_limits=["15/minute", "200/hour", "1000/day"]
)


# from functools import wraps

# from fastapi import HTTPException, Request

# from app.core.cache import Cache


# async def _rate_limiter(request: Request, limit: int, window: int):
#     ip = request.client.host if request.client else "unknown"
#     route = request.scope.get("route")
#     path = route.path if route else request.url.path

#     key = f"rate:{ip}:{path}"

#     count = await Cache.incr(key)

#     if count == 1:
#         await Cache.expire(key, window)

#     if count > limit:
#         raise HTTPException(status_code=429, detail="Too Many Requests")


# def rate_limiter(limit: int = 100, window: int = 60):
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             request: Request | None = kwargs.get("request")

#             if request is None:
#                 for arg in args:
#                     if isinstance(arg, Request):
#                         request = arg
#                         break

#             if request is None:
#                 raise RuntimeError("Request is required for rate limiting")

#             await _rate_limiter(request, limit, window)

#             return await func(*args, **kwargs)

#         return wrapper

#     return decorator
