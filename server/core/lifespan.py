from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from core.cache import cache_lifespan
from scripts.seed import run_seed

LIFESPAN_REGISTRY = [
    cache_lifespan,
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_seed()

    async with AsyncExitStack() as stack:
        for lifespan_fn in LIFESPAN_REGISTRY:
            await stack.enter_async_context(lifespan_fn(app))

        yield
