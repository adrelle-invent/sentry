from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from app.core.cache import cache_lifespan

LIFESPAN_REGISTRY = [
    cache_lifespan,
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        for lifespan_fn in LIFESPAN_REGISTRY:
            await stack.enter_async_context(lifespan_fn(app))

        yield
