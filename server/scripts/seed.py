import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_factory
from core.logger import get_logger
from core.utils import slugify
from modules.telemetry.models.access_key import AccessKey
from modules.telemetry.models.service import (
    Service,
    ServiceEnvironment,
    ServiceStatus,
)
from modules.telemetry.services.access_key_service import generate_access_key
from modules.tenancy.models import User, UserRole, Workspace

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Seed constants — override via environment variables as needed
# ---------------------------------------------------------------------------
SEED_WORKSPACE_NAME = "AD. Sentry"
SEED_WORKSPACE_SLUG = slugify(SEED_WORKSPACE_NAME)

SEED_USER_EMAIL = "test@example.com"
SEED_USER_PASSWORD = "password"
SEED_USER_FIRST = "John"
SEED_USER_LAST = "Doe"

SEED_SERVICE_NAME = "sentry-api"
SEED_SERVICE_SLUG = "svc_sentry_api"

SEED_ACCESS_KEY_NAME = "private_access_key"


def _hash_password(raw: str) -> str:
    """SHA-256 hex digest (no bcrypt installed). Replace with bcrypt in prod."""
    return hashlib.sha256(raw.encode()).hexdigest()


async def run_seed() -> None:
    async with async_session_factory() as db:
        await _seed_workspace(db)
        await db.commit()


async def _seed_workspace(db: AsyncSession) -> None:
    # ---- Workspace --------------------------------------------------------
    workspace_result = await db.execute(
        select(Workspace).where(Workspace.slug == SEED_WORKSPACE_SLUG)
    )
    workspace = workspace_result.scalar_one_or_none()

    if workspace is None:
        workspace = Workspace(
            id=uuid.uuid4(),
            name=SEED_WORKSPACE_NAME,
            slug=SEED_WORKSPACE_SLUG,
        )
        db.add(workspace)
        await db.flush()  # populate workspace.id before FK refs
        logger.info("seed_workspace_created", slug=SEED_WORKSPACE_SLUG)
    else:
        logger.info("seed_workspace_exists", slug=SEED_WORKSPACE_SLUG)

    # ---- User -------------------------------------------------------------
    user_result = await db.execute(
        select(User).where(User.email == SEED_USER_EMAIL)
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        user = User(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            email=SEED_USER_EMAIL,
            password=_hash_password(SEED_USER_PASSWORD),
            first_name=SEED_USER_FIRST,
            last_name=SEED_USER_LAST,
            avatar_url="",
            role=UserRole.owner,
            is_active=True,
            email_verified_at=datetime.now(UTC),
        )
        db.add(user)
        await db.flush()
        logger.info("seed_user_created", email=SEED_USER_EMAIL, role=UserRole.owner)
    else:
        logger.info("seed_user_exists", email=SEED_USER_EMAIL)

    # ---- Service ----------------------------------------------------------
    service_result = await db.execute(
        select(Service).where(Service.slug == SEED_SERVICE_SLUG)
    )
    service = service_result.scalar_one_or_none()

    if service is None:
        service = Service(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            slug=SEED_SERVICE_SLUG,
            name=SEED_SERVICE_NAME,
            environment=ServiceEnvironment.development,
            status=ServiceStatus.active,
        )
        db.add(service)
        await db.flush()
        logger.info(
            "seed_service_created",
            slug=SEED_SERVICE_SLUG,
            name=SEED_SERVICE_NAME,
        )
    else:
        logger.info("seed_service_exists", slug=SEED_SERVICE_SLUG)

    # ---- Access Key -------------------------------------------------------
    existing_key_result = await db.execute(
        select(AccessKey).where(
            AccessKey.workspace_id == workspace.id,
            AccessKey.name == SEED_ACCESS_KEY_NAME,
        )
    )
    existing_key = existing_key_result.scalar_one_or_none()

    if existing_key is None:
        full_key, prefix, key_hash = generate_access_key()
        access_key = AccessKey(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            name=SEED_ACCESS_KEY_NAME,
            key_prefix=prefix,
            key_hash=key_hash,
            allowed_services={
                str(service.id): True
            },
            is_active=True,
        )
        db.add(access_key)
        # Log the plaintext key ONCE — it is never retrievable again
        logger.warning(
            "seed_access_key_created",
            name=SEED_ACCESS_KEY_NAME,
            full_key=full_key,
        )
    else:
        logger.info("seed_access_key_exists", name=SEED_ACCESS_KEY_NAME)
