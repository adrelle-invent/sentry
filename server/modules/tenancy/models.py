import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from modules.users.models import User


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    users: Mapped[list[User]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    services: Mapped[list["Service"]] = relationship(   # noqa: F821 # type: ignore
        back_populates="workspace", cascade="all, delete-orphan"
    )


