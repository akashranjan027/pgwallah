"""
Database configuration and connection management
"""
import asyncio
from typing import AsyncGenerator

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
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
            "pk": "pk_%(table_name)s"
        }
    )


# Create async engine
engine = create_async_engine(
    settings.database_url_str,
    echo=settings.DEBUG and not settings.is_testing,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1 hour
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Yields an async session and ensures it's properly closed.
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
    """Create all tables in the database"""
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


class DatabaseManager:
    """Database manager for handling connections and health checks"""
    
    def __init__(self) -> None:
        self._engine = engine
        self._session_maker = AsyncSessionLocal

    async def health_check(self) -> dict[str, str]:
        """Perform health check on database"""
        try:
            is_connected = await check_db_connection()
            return {
                "status": "healthy" if is_connected else "unhealthy",
                "database": "postgresql",
                "connection": "active" if is_connected else "failed"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "postgresql",
                "connection": "failed",
                "error": str(e)
            }

    async def close(self) -> None:
        """Close database connections"""
        await self._engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()