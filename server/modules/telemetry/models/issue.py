import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import UUID, DateTime, Float, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Issue(Base):
    __tablename__="issues"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    title: Mapped[str] = mapped_column(String, nullable=False)
    endpoint: Mapped[str | None] = mapped_column(String, nullable=True)
    method: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
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
    severity: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list | dict | None] = mapped_column(
        JSONB, nullable=True
    )

    # 1536-dimensional vector for OpenAI text-embedding-3-small or similar models
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(dim=1536),
        nullable=True,
    )
