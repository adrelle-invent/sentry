from typing import Any

from pydantic import Field

from core.database import Base


class EventCreate(Base):
    service: str = Field(..., json_schema_extra={"example": "chat-api"})
    environment: str = Field(..., json_schema_extra={"example": "production"})
    level: str = Field(..., json_schema_extra={"example": "ERROR"})
    event_message: str
    trace_id: str | None = None
    metadata: dict[str, Any] | None = None


class EventResponse(EventCreate):
    id: str
    created_at: str


class Pagination(Base):
    limit: int = Field(default=100, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class Filters(Base):
    service: str | None = None
    level: str | None = None
