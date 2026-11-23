import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.base_model import Base, TenantMixin, UUIDMixin
from modules.telemetry.enums import EventLevel


class Event(Base, UUIDMixin, TenantMixin):
    __tablename__ = "events"

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issue_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    trace_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    level: Mapped[EventLevel] = mapped_column(
        Enum(EventLevel, name="event_level", native_enum=True),
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    attributes: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
