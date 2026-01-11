"""
System log pruning worker.

Runs daily at 02:00 local time to prune log entries beyond retention.
"""

import asyncio
import logging
import os
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.adapters.postgres.unit_of_work import SqlAlchemyUnitOfWork
from app.application.services.system_log_service import SystemLogService
from app.logging_config import configure_logging

configure_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


async def prune_logs_worker():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")

    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

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

    logger.info("Log pruning worker started")
    last_run_date = None

    while True:
        now = datetime.now()
        if now.hour == 2 and now.minute == 0:
            if last_run_date != now.date():
                try:
                    async with async_session_factory() as session:
                        uow = SqlAlchemyUnitOfWork(session)
                        service = SystemLogService(uow)
                        deleted = await service.prune_logs()
                        logger.info("Pruned %s log entries", deleted)
                    last_run_date = now.date()
                except Exception as exc:
                    logger.error("Log pruning failed: %s", exc, exc_info=True)
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(prune_logs_worker())
