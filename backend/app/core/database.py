from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    pass


def create_engine():
    kwargs = {
        "echo": settings.DEBUG,
        "pool_pre_ping": True,
    }

    if settings.ENVIRONMENT == "testing":
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
        kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
        kwargs["pool_timeout"] = settings.DATABASE_POOL_TIMEOUT
        kwargs["pool_recycle"] = settings.DATABASE_POOL_RECYCLE

    return create_async_engine(settings.DATABASE_URL, **kwargs)


engine = create_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    logger.info("Initializing database connection")
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(
            __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector")
        )
        logger.info("pgvector extension enabled")
    logger.info("Database initialized successfully")


async def close_db() -> None:
    logger.info("Closing database connections")
    await engine.dispose()
    logger.info("Database connections closed")
