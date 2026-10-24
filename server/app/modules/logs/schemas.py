from typing import Any

from pydantic import BaseModel, Field


class LogCreate(BaseModel):
    service: str = Field(..., json_schema_extra={"example": "chat-api"})
    environment: str = Field(..., json_schema_extra={"example": "production"})
    level: str = Field(..., json_schema_extra={"example": "ERROR"})
    log_message: str
    trace_id: str | None = None
    metadata: dict[str, Any] | None = None


class LogResponse(LogCreate):
    id: str
    created_at: str


class LogQueryFilter(BaseModel):
    service: str | None = None
    level: str | None = None
    limit: int = Field(default=100, ge=1, le=100)
