
from sqlalchemy import func, select
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select

from core.cache import CacheDep
from core.database import SessionDep, TxSessionDep
from core.logger import get_logger
from modules.telemetry.exceptions import EventNotFoundError
from modules.telemetry.models.event import Event
from modules.telemetry.schemas import EventCreate, Filters, Pagination

logger = get_logger(__name__)


class EventService:
    def __init__(self, cache: CacheDep) -> None:
        self.cache = cache

    # TODO: fix return type
    async def get_events(
        self, db: AsyncSession, filters: Filters, pagination: Pagination
    ) -> dict:
        async def _fetch_from_db():
            query: Select[tuple[Event]] = (
                select(Event)
                .order_by(Event.created_at.desc())
                .limit(pagination.limit)
                .offset(pagination.offset)
            )

            count_query = select(func.count()).select_from(Event)

            if filters.service:
                query = query.where(Event.service_id == filters.service)
                count_query = count_query.where(
                    Event.service_id == filters.service
                )

            if filters.level:
                query = query.where(Event.level == filters.level)
                count_query = count_query.where(Event.level == filters.level)

            result: Result[tuple[Event]] = await db.execute(query)

            total_result = await db.execute(count_query)
            total = total_result.scalar_one()

            return {
                "data": result.scalars().all(),
                "limit": pagination.limit,
                "offset": pagination.offset,
                "total": total,
            }

        return await self.cache.get_or_set_with_lock(
            f"events:service:{filters.service}:level:{filters.level}:limit:{pagination.limit}:offset:{pagination.offset}",
            _fetch_from_db,
        )

    async def get_event(self, db: SessionDep, event_id: str) -> dict:
        not_found_key = f"events:not_found:{event_id}"

        if await self.cache.has(not_found_key):
            raise EventNotFoundError(f"Event with id {event_id} not found")

        async def _fetch_from_db():
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

    async def create_event(
        self, db: TxSessionDep, event_data: EventCreate
    ) -> dict:
        # TODO: move to worker (batched)
        db.add(Event(**event_data.model_dump()))
        return {"status": "success", "queue_id": "msg_id"}
