from redis.asyncio import Redis

from app.config import settings
from app.shared.logger import get_logger

logger = get_logger(__name__)

# Global connection pool
redis = Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    decode_responses=True,
    protocol=2,
)


class Cache:
    def __init__(self, client: Redis):
        self.client = client

    async def ping(self) -> None:
        """ping"""
        try:
            await self.client.ping()
            logger.info("redis_connection_established")
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            raise RuntimeError(
                f"Critical infrastructure failure: Could not connect to Redis. {e}"
            ) from e

    async def close(self) -> None:
        """Gracefully close the Redis connection pool on shutdown."""
        await self.client.close()
        logger.info("redis_connection_closed_gracefully")

    async def set(self, key: str, value: str, expire_seconds: int = 60) -> None:
        try:
            await self.client.set(key, value, ex=expire_seconds)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def get(self, key: str) -> str | None:
        try:
            return await self.client.get(key)  # type: ignore
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

    async def clear(self) -> bool:
        """Clear the current Redis database safely."""
        try:
            await self.client.flushdb()
            logger.info("redis_cache_cleared")
            return True
        except Exception as e:
            logger.exception("cache_clear_error", error=str(e))
            return False


cache = Cache(client=redis)
