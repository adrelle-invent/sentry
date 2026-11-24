
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.base_model import Base, TenancyMixin, TimestampMixin, UUIDMixin
from modules.telemetry.enums import ServiceEnvironment, ServiceStatus
from modules.tenancy.models import Workspace


class Service(Base, UUIDMixin, TimestampMixin, TenancyMixin):
    __tablename__ = "services"

    slug: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    environment: Mapped[ServiceEnvironment] = mapped_column(
        Enum(ServiceEnvironment, name="service_environment", native_enum=True),
        nullable=False,
    )
    status: Mapped[ServiceStatus] = mapped_column(
        Enum(ServiceStatus, name="service_status", native_enum=True),
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="services")
