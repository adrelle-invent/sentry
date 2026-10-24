import json
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from redis import RedisError
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

redis = Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    decode_responses=True,
    protocol=2,
    socket_timeout=5.0,
    socket_connect_timeout=3.0,
    health_check_interval=30,
)


@asynccontextmanager
async def cache_lifespan(app: FastAPI):
    """Ensure Redis connection is established before application starts."""
    try:
        await redis.ping()
        logger.info("redis_connection_established")
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        raise RuntimeError(
            f"Critical infrastructure failure: Could not connect to Redis. {e}"
        ) from e

    yield

    """Gracefully close the Redis connection pool on shutdown."""
    await redis.close()
    logger.info("redis_connection_closed_gracefully")


class Cache:
    def __init__(self, client: Redis):
        self.client = client

    async def set(self, key: str, value: Any, expire_seconds: int = 60) -> None:
        try:
            # Serialize dictionaries, lists, or pydantic models into a string format for Redis
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            elif hasattr(value, "model_dump_json"):  # Pydantic v2
                serialized = value.model_dump_json()
            elif hasattr(value, "dict"):  # Pydantic v1 fallback
                serialized = json.dumps(value.dict())
            else:
                serialized = str(value)

            await self.client.set(key, serialized, ex=expire_seconds)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def get(self, key: str) -> Any | None:
        try:
            data = await self.client.get(key)
            if not data:
                return None

            decoded = data.decode("utf-8") if isinstance(data, bytes) else data

            try:
                return json.loads(decoded)
            except (json.JSONDecodeError, TypeError):
                return decoded

        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    async def has(self, key: str) -> bool:
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.warning(f"Cache check error: {e}")
            return False

    async def forget(self, key: str) -> None:
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")

    async def incr(self, key: str) -> int | None:
        try:
            return await self.client.incr(key)  # type: ignore
        except Exception as e:
            logger.warning(f"Cache incr error: {e}")
            return None

    async def expire(self, key: str, ttl: int) -> bool:
        try:
            return bool(await self.client.expire(key, ttl))
        except Exception as e:
            logger.warning(f"Cache expire error: {e}")
            return False

    async def get_or_set_with_lock(
        self,
        key: str,
        fetch_func: Callable[[], Awaitable[Any]],
        expire_seconds: int = 60,
        lock_timeout: float = 5.0,
        blocking_timeout: float = 2.0,
    ) -> Any:
        """
        Implements cache-aside with a distributed lock to prevent cache stampedes.
        """
        cached_val = await self.get(key)
        if cached_val is not None:
            return cached_val

        lock_key = f"lock:{key}"

        try:
            async with self.client.lock(
                lock_key,
                timeout=lock_timeout,
                blocking_timeout=blocking_timeout,
            ):
                cached_val = await self.get(key)
                if cached_val is not None:
                    return cached_val

                fresh_val = await fetch_func()

                if fresh_val is not None:
                    await self.set(
                        key, fresh_val, expire_seconds=expire_seconds
                    )

                return fresh_val

        except RedisError as e:
            logger.warning("redis_lock_error_fallback", key=key, error=str(e))
            return await fetch_func()


cache = Cache(client=redis)


def get_cache() -> Cache:
    return cache


CacheDep = Annotated[Cache, Depends(get_cache)]
