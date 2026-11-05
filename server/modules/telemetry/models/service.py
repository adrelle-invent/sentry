import enum
import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ServiceEnvironment(enum.StrEnum):
    development = "development"
    staging = "staging"
    production = "production"


class ServiceStatus(enum.StrEnum):
    active = "active"
    inactive = "inactive"


class Service(Base):
    __tablename__ = "services"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    public_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    environment: Mapped[ServiceEnvironment] = mapped_column(
        Enum(ServiceEnvironment, name="service_environment"), nullable=False
    )
    status: Mapped[ServiceStatus] = mapped_column(
        Enum(ServiceStatus, name="service_status"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
