from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaginatedResponse[T](BaseModel):
    data: list[T]
    total: int
    limit: int
    offset: int


class Pagination(BaseModel):
    limit: int = Field(default=100, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class Filters(BaseModel):
    service: str | None = None
    level: str | None = None


class EventCreate(BaseModel):
    service: str = Field(..., json_schema_extra={"example": "chat-api"})
    environment: str = Field(..., json_schema_extra={"example": "production"})
    level: str = Field(..., json_schema_extra={"example": "ERROR"})
    event_message: str
    trace_id: str | None = None
    attributes: dict[str, Any] | None = None


class EventResponse(EventCreate):
    id: UUID
    workspace_id: UUID
    service_id: UUID
    issue_id: UUID | None = None
    trace_id: str | None = None
    level: str
    message: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccessKeyCreate(BaseModel):
    name: str = Field(..., max_length=100)
    allowed_services: dict[str, str] = Field(default_factory=dict)
    expires_at: datetime | None = None


class AccessKeyResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    key_prefix: str
    allowed_services: dict[str, str]
    is_active: bool
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccessKeyCreateResponse(AccessKeyResponse):
    raw_key: str
