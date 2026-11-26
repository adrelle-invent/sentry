import json
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated, Any, TypeVar

from fastapi import Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from redis import RedisError
from redis.asyncio import Redis

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

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

    def _serialize_value(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if hasattr(value, "model_dump_json"):
            return value.model_dump_json()
        return json.dumps(jsonable_encoder(value))

    def _deserialize_value(self, raw: str | bytes | None) -> Any:
        if raw is None:
            return None
        text = raw.decode() if isinstance(raw, bytes) else raw
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    async def set(self, key: str, value: Any, expire_seconds: int = 60) -> None:
        try:
            serialized = self._serialize_value(value)
            await self.client.set(key, serialized, ex=expire_seconds)
        except Exception as e:
            logger.warning("Cache write error for key=%s: %s", key, e)

    async def get(self, key: str) -> Any:
        try:
            data = await self.client.get(key)
            if data is None:
                return None
            return self._deserialize_value(data)
        except Exception as e:
            logger.warning("Cache read error for key=%s: %s", key, e)
            return None

    async def has(self, key: str) -> bool:
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.warning("Cache check error for key=%s: %s", key, e)
            return False

    async def forget(self, key: str) -> None:
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.warning("Cache delete error for key=%s: %s", key, e)

    async def incr(self, key: str) -> int | None:
        try:
            return await self.client.incr(key)  # type: ignore
        except Exception as e:
            logger.warning("Cache incr error for key=%s: %s", key, e)
            return None

    async def expire(self, key: str, ttl: int) -> bool:
        try:
            return bool(await self.client.expire(key, ttl))
        except Exception as e:
            logger.warning("Cache expire error for key=%s: %s", key, e)
            return False


    async def get_or_set_with_lock(
        self,
        key: str,
        fetch_func: Callable[[], Awaitable[T]],
        expire_seconds: int = 60,
        lock_timeout: float = 5.0,
        blocking_timeout: float = 2.0,
    ) -> T:
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
