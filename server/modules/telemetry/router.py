from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from core.database import SessionDep, TxSessionDep
from modules.telemetry.schemas import (
    EventCreate,
    EventResponse,
    Filters,
    PaginatedResponse,
    Pagination,
)
from modules.telemetry.services.event_service import EventService

router = APIRouter(prefix="/events")

EventServiceDep = Annotated[EventService, Depends()]


@router.get("", response_model=PaginatedResponse[EventResponse])
async def index(
    request: Request,
    db: SessionDep,
    event_service: EventServiceDep,
    pagination: Annotated[Pagination, Query()],
    filters: Annotated[Filters, Query()],
):
    result = await event_service.get_events(
        db=db, pagination=pagination, filters=filters
    )

    offset, limit, total = result["offset"], result["limit"], result["total"]
    next_offset = offset + limit if offset + limit < total else None
    prev_offset = max(0, offset - limit) if offset > 0 else None

    def cursor_url(new_offset: int | None) -> str | None:
        if new_offset is None:
            return None
        return str(request.url.include_query_params(offset=new_offset))

    return {
        **result,
        "next": cursor_url(next_offset),
        "prev": cursor_url(prev_offset),
    }

@router.get("/{event_id}", response_model=EventResponse)
async def show(
    request: Request,
    db: SessionDep,
    event_service: EventServiceDep,
    event_id: str,
):
    return await event_service.get_event(db=db, event_id=event_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def store(
    request: Request,
    db: TxSessionDep,
    event_service: EventServiceDep,
    event: EventCreate,
):
    return await event_service.create_event(db=db, event_data=event)
