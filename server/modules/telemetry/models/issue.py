import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    UUID,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.base_model import Base, TenancyMixin, TimestampMixin, UUIDMixin


class Issue(Base, UUIDMixin, TimestampMixin, TenancyMixin):
    __tablename__ = "issues"

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    fingerprint: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="open"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)
    method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    evidence: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    occurrence_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1", default=1
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    scenario: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list | dict | None] = mapped_column(
        JSON, nullable=True
    )

    # 1536-dimensional vector for OpenAI text-embedding-3-small
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(dim=1536),
        nullable=True,
    )

    events: Mapped[list["Event"]] = relationship(
        back_populates="issue",
        cascade="all, delete-orphan",
    )
