import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import insert

from app.core.database import async_session_factory
from app.modules.logs.models import LogModel


# TODO: validate
class LogBatchWorker:
    def __init__(
        self, batch_size: int = 100, flush_interval: float = 2.0
    ) -> None:
        self.queue: asyncio.Queue[dict] = asyncio.Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Starts the background worker loop when FastAPI boots up."""
        self._task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        """Gracefully shuts down the worker and flushes any remaining logs."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            await self._flush_remaining()

    async def push(self, log_data: dict) -> None:
        """Instantly queues a log without blocking the HTTP response."""
        await self.queue.put(log_data)

    async def _worker_loop(self) -> None:
        buffer: list[dict] = []
        last_flush_time = asyncio.get_running_loop().time()

        while True:
            try:
                # Calculate remaining time for the 2-second window
                elapsed = asyncio.get_running_loop().time() - last_flush_time
                timeout = max(0.05, self.flush_interval - elapsed)

                # Wait for the next log item or hit the 2-second timeout
                item = await asyncio.wait_for(self.queue.get(), timeout=timeout)
                buffer.append(item)
                self.queue.task_done()

                # If we hit 100 items, flush immediately
                if len(buffer) >= self.batch_size:
                    await self._flush(buffer)
                    buffer.clear()
                    last_flush_time = asyncio.get_running_loop().time()

            except TimeoutError:
                # 2 seconds expired! Flush whatever we have accumulated so far
                if buffer:
                    await self._flush(buffer)
                    buffer.clear()
                    last_flush_time = asyncio.get_running_loop().time()

    async def _flush(self, buffer: list[dict]) -> None:
        """Executes the ultra-fast bulk insert into PostgreSQL."""
        async with async_session_factory() as db:
            async with db.begin():
                await db.execute(insert(LogModel), buffer)

    async def _flush_remaining(self) -> None:
        """Ensures zero log loss when the server stops."""
        buffer = []
        while not self.queue.empty():
            buffer.append(self.queue.get_nowait())
            self.queue.task_done()
        if buffer:
            await self._flush(buffer)


# Global instance to share across your app
log_worker = LogBatchWorker(batch_size=100, flush_interval=2.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await log_worker.start()
    yield
    await log_worker.stop()
