from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from common.pagination import PaginationParams, build_pagination_meta
from core.database import SessionDep
from modules.telemetry.schemas.event import (
    EventCreate,
    EventFilterParams,
    EventResponse,
    PaginatedEventsResponse,
)
from modules.telemetry.services.event_service import EventService

router = APIRouter(prefix="/events")

EventServiceDep = Annotated[EventService, Depends()]


@router.get("", response_model=PaginatedEventsResponse[EventResponse])
async def index(
    request: Request,
    db: SessionDep,
    event_service: EventServiceDep,
    pagination: Annotated[PaginationParams, Query()],
    filters: Annotated[EventFilterParams, Query()],
):
    result = await event_service.get_events(
        db=db, pagination=pagination, filters=filters
    )

    meta = build_pagination_meta(
        page=result["page"],
        size=result["size"],
        total=result["total"],
        url=request.url,
    )

    return {**result, **meta}


@router.get("/{event_id}", response_model=EventResponse)
async def show(
    request: Request,
    db: SessionDep,
    event_service: EventServiceDep,
    event_id: UUID,
):
    return await event_service.get_event(db=db, event_id=event_id)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def store(
    request: Request,
    event_service: EventServiceDep,
    event: EventCreate,
):
    return await event_service.create_event(event_data=event)
