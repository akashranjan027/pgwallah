"""
Database configuration and connection management for Orders service
"""
from typing import AsyncGenerator

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all database models"""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


# Create async engine
engine = create_async_engine(
    settings.database_url_str,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
    # Pool sizes are ignored by SQLite drivers but work for Postgres
    pool_size=settings.DB_POOL_SIZE if settings.database_url_str.startswith(("postgresql+", "mysql+")) else None,  # type: ignore[arg-type]
    max_overflow=settings.DB_MAX_OVERFLOW if settings.database_url_str.startswith(("postgresql+", "mysql+")) else None,  # type: ignore[arg-type]
    pool_timeout=settings.DB_POOL_TIMEOUT if settings.database_url_str.startswith(("postgresql+", "mysql+")) else None,  # type: ignore[arg-type]
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Ensures the session is properly closed and rolled back on error.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables in the database (for SQLite/local dev)"""
    # Import models so they are registered with the Base before create_all
    from app.models.order import Order, OrderItem, KitchenStation, OrderSequence  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all tables in the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_db_connection() -> bool:
    """Check if database connection is healthy"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False