"""Database session management and initialization.

This module provides async database session factory and initialization utilities.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from config import get_settings
from database.models import Base


settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database by creating all tables.

    This function should be called on application startup to ensure
    all database tables exist.
    """
    settings.ensure_data_dir()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.

    Yields:
        AsyncSession instance for database operations.

    Example:
        ```python
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db() -> None:
    """Close database connections.

    This function should be called on application shutdown.
    """
    await engine.dispose()
