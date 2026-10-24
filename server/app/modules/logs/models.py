import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LogModel(Base):
    __tablename__ = "logs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    service: Mapped[str] = mapped_column(String, nullable=False)
    environment: Mapped[str] = mapped_column(String, nullable=False)
    level: Mapped[str] = mapped_column(String, nullable=False)
    log_message: Mapped[str] = mapped_column(Text, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String, nullable=True)
    log_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "service": self.service,
            "environment": self.environment,
            "level": self.level,
            "log_message": self.log_message,
            "trace_id": self.trace_id,
            "metadata": self.log_metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    async def create(cls, db: AsyncSession, log: "LogModel") -> "LogModel":
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log
