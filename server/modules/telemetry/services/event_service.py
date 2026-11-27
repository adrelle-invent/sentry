from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select

from common.pagination import PaginationParams
from core.cache import CacheDep
from core.database import SessionDep
from core.logger import get_logger
from modules.telemetry.exceptions import EventNotFoundError
from modules.telemetry.models.event import Event
from modules.telemetry.schemas.event import (
    EventCreate,
    EventFilterParams,
)

logger = get_logger(__name__)


class EventService:
    def __init__(self, cache: CacheDep) -> None:
        self.cache = cache

    async def get_events(
        self,
        db: AsyncSession,
        filters: EventFilterParams,
        pagination: PaginationParams,
    ) -> dict:
        async def _fetch_from_db():
            offset = (pagination.page - 1) * pagination.size

            query: Select[tuple[Event]] = (
                select(Event)
                .order_by(Event.created_at.desc())
                .offset(offset)
                .limit(pagination.size)
            )

            count_query = select(func.count()).select_from(Event)

            if filters.service_id:
                query = query.where(Event.service_id == filters.service_id)
                count_query = count_query.where(
                    Event.service_id == filters.service_id
                )

            if filters.level:
                query = query.where(Event.level == filters.level)
                count_query = count_query.where(Event.level == filters.level)

            result = await db.execute(query)

            total_result = await db.execute(count_query)
            total = total_result.scalar_one()

            return {
                "items": result.scalars().all(),
                "page": pagination.page,
                "size": pagination.size,
                "total": total,
            }

        return await self.cache.get_or_set_with_lock(
            f"events:service::{filters.service_id}:level:{filters.level}:size:{pagination.size}:page:{pagination.page}",
            _fetch_from_db,
        )

    async def get_event(self, db: SessionDep, event_id: UUID) -> Event:
        not_found_key = f"events:not_found:{event_id}"

        if await self.cache.has(not_found_key):
            raise EventNotFoundError(f"Event with id {event_id} not found")

        async def _fetch_from_db() -> Event:
            result = await db.execute(select(Event).where(Event.id == event_id))
            event = result.scalar_one_or_none()

            if not event:
                await self.cache.set(not_found_key, "1", expire_seconds=30)
                raise EventNotFoundError(f"Event with id {event_id} not found")

            return event

        return await self.cache.get_or_set_with_lock(
            f"event:{event_id}",
            _fetch_from_db,
            expire_seconds=60,
        )

    async def create_event(self, event_data: EventCreate) -> dict:
        stream_id = await self.cache.xadd("events", event_data.model_dump(mode="json"))
        return {"status": "success", "queue_id": stream_id}
