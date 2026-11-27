import asyncio
import json
import signal
from typing import Any

from redis.asyncio import Redis, ResponseError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import models  # noqa: F401
from core.cache import redis
from core.database import async_session_factory, engine
from core.logger import get_logger
from modules.telemetry.models.event import Event

logger = get_logger(__name__)

STREAM_KEY = "events"
GROUP_NAME = "telemetry-events"
CONSUMER_NAME = "events-worker-1"

BATCH_SIZE = 50
BLOCK_MS = 2000
MIN_IDLE_MS = 30000
RECLAIM_INTERVAL_SEC = 10.0


def decode_payload(fields: dict[Any, Any]) -> dict[str, Any]:
    raw_payload = fields.get("payload") or fields.get(b"payload")
    if raw_payload is None:
        raise ValueError("Missing 'payload' field in stream entry")

    if isinstance(raw_payload, bytes):
        text = raw_payload.decode("utf-8")
    else:
        text = str(raw_payload)

    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Decoded payload must be a JSON object")
    return parsed


async def ensure_consumer_group(redis: Redis) -> None:
    try:
        await redis.xgroup_create(
            name=STREAM_KEY,
            groupname=GROUP_NAME,
            id="0",
            mkstream=True,
        )
        logger.info(
            "Created consumer group '%s' on stream '%s'", GROUP_NAME, STREAM_KEY
        )
    except ResponseError as exc:
        if "BUSYGROUP" in str(exc):
            logger.debug("Consumer group '%s' already exists", GROUP_NAME)
        else:
            raise


async def process_entry(
    redis: Redis,
    async_session_factory: async_sessionmaker[AsyncSession],
    entries
) -> None:
    stream_ids = []
    batch = []

    for stream_id, entry in entries:
        stream_ids.append(stream_id)
        batch.append(Event(**decode_payload(entry)))

    async with async_session_factory() as session:
        async with session.begin():
            session.add_all(batch)

        logger.debug("Persisted %d telemetry events", len(batch))

    await redis.xack(STREAM_KEY, GROUP_NAME, *stream_ids)


async def reclaim_pending_entries(
    redis: Redis,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    next_start_id = "0-0"
    while True:
        # redis-py xautoclaim returns (next_start_id, claimed_entries, deleted_ids)
        next_start_id, claimed_entries, _ = await redis.xautoclaim(
            name=STREAM_KEY,
            groupname=GROUP_NAME,
            consumername=CONSUMER_NAME,
            min_idle_time=MIN_IDLE_MS,
            start_id=next_start_id,
            count=BATCH_SIZE,
        )

        if not claimed_entries:
            break

        # TODO: catch exceptions
        await process_entry(
            redis, async_session_factory, claimed_entries
        )

        if next_start_id in ("0-0", b"0-0"):
            break


async def run_worker() -> None:
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    last_reclaim = 0.0

    try:
        await ensure_consumer_group(redis)
        logger.info(
            "Worker started stream=%s group=%s consumer=%s",
            STREAM_KEY,
            GROUP_NAME,
            CONSUMER_NAME,
        )

        while not stop_event.is_set():
            now = loop.time()
            if now - last_reclaim >= RECLAIM_INTERVAL_SEC:
                last_reclaim = now
                try:
                    await reclaim_pending_entries(redis, async_session_factory)
                except Exception:
                    logger.exception("Error reclaiming pending entries")

            streams = await redis.xreadgroup(
                groupname=GROUP_NAME,
                consumername=CONSUMER_NAME,
                streams={STREAM_KEY: ">"},
                count=BATCH_SIZE,
                block=BLOCK_MS,
            )

            if not streams:
                continue

            for _stream_name, entries in streams:
                # TODO: catch exceptions
                await process_entry(redis, async_session_factory, entries)
    finally:
        logger.info("Shutting down worker %s...", CONSUMER_NAME)
        await redis.aclose()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_worker())
