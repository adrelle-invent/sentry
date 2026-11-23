from sqlalchemy import (
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.base_model import Base, TimestampMixin, UUIDMixin
from modules.users.models import User


class Workspace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workspaces"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )

    users: Mapped[list[User]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    services: Mapped[list["Service"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="workspace", cascade="all, delete-orphan"
    )
