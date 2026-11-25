from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from common.pagination import PaginatedResponse
from modules.telemetry.enums import EventLevel


class EventBase(BaseModel):
    workspace_id: UUID
    service_id: UUID
    issue_id: UUID | None = None
    trace_id: str | None = Field(None, max_length=64)
    level: EventLevel
    message: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedEventsResponse(PaginatedResponse):
    items: list[EventResponse]

class EventFilterParams(BaseModel):
    service_id: UUID | None = None
    level: EventLevel | None = None