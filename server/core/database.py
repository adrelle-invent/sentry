from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from core.config import settings

engine: AsyncEngine = create_async_engine(
    url=settings.database_url,  # e.g. postgresql+asyncpg://user:pass@host:5432/dbname
    echo=False,
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
    expire_on_commit=False,  # CRITICAL for async workflows
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
