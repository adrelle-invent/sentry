import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class EventLevel(enum.StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id"), nullable=False
    )
    issue_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("issues.id"), nullable=True
    )
    trace_id: Mapped[str | None] = mapped_column(String, nullable=True)
    level: Mapped[EventLevel] = mapped_column(
        Enum(EventLevel, name="event_level"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "service_id": str(self.service_id),
            "issue_id": str(self.issue_id) if self.issue_id else None,
            "trace_id": self.trace_id,
            "level": self.level.value
            if isinstance(self.level, EventLevel)
            else self.level,
            "message": self.message,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat(),
        }
