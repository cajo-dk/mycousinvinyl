"""
Cache cleanup worker.

Periodically removes expired Discogs cache entries to prevent database bloat.
Runs hourly in the background.
"""

import asyncio
import logging
import os
from datetime import datetime

from app.adapters.postgres.discogs_cache_repository_adapter import PostgresDiscogsCacheRepository
from app.adapters.postgres.system_log_repository_adapter import SystemLogRepositoryAdapter
from app.domain.entities import SystemLogEntry
from app.logging_config import configure_logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

configure_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


async def cleanup_cache_worker():
    """Hourly worker to clean up expired cache entries."""
    # Get database URL from environment (this worker doesn't need other settings)
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")

    # Convert postgresql:// to postgresql+asyncpg:// for async driver
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

    # Create engine and session factory
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )

    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    logger.info("Cache cleanup worker started")

    while True:
        try:
            async with async_session_factory() as session:
                cache_repo = PostgresDiscogsCacheRepository(session)
                count = await cache_repo.cleanup_expired()
                logger.info(f"Cleaned up {count} expired cache entries at {datetime.now()}")
                log_repo = SystemLogRepositoryAdapter(session)
                await log_repo.create(SystemLogEntry(
                    user_id=None,
                    user_name="*system",
                    severity="INFO",
                    component="Cache Cleanup",
                    message=f"Cache cleanup removed {count} expired entries",
                ))
                await session.commit()
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}", exc_info=True)
            try:
                async with async_session_factory() as session:
                    log_repo = SystemLogRepositoryAdapter(session)
                    await log_repo.create(SystemLogEntry(
                        user_id=None,
                        user_name="*system",
                        severity="ERROR",
                        component="Cache Cleanup",
                        message=f"Cache cleanup failed: {e}",
                    ))
                    await session.commit()
            except Exception:
                logger.error("Failed to log cache cleanup error", exc_info=True)

        # Sleep for 1 hour
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(cleanup_cache_worker())
