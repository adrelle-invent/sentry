from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Explicit naming convention for constraints (crucial for Alembic)
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)


engine: AsyncEngine = create_async_engine(
    url=settings.database_url,  # e.g. postgresql+asyncpg://user:pass@host:5432/dbname
    echo=settings.DB_ECHO_LOG,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True,  # Tests connection liveness before checkout
    pool_recycle=1800,  # Recycle connections every 30 mins
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # CRITICAL fmr async workflows
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_tx_db(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    async with session.begin():
        yield session


# Type Aliases
SessionDep = Annotated[AsyncSession, Depends(get_db)]
TxSessionDep = Annotated[AsyncSession, Depends(get_tx_db)]
