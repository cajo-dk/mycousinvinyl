"""
Alembic migration runner for automatic upgrades.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.adapters.postgres.unit_of_work import SqlAlchemyUnitOfWork
from app.application.services.system_log_service import SystemLogService
from app.adapters.postgres.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


def _build_alembic_config() -> Config:
    root = Path(__file__).resolve().parents[3]
    ini_path = root / "alembic.ini"
    config = Config(str(ini_path))
    config.set_main_option("script_location", str(root / "alembic"))
    return config


def _run_migrations_sync() -> None:
    config = _build_alembic_config()
    command.upgrade(config, "head")


def _stamp_head_sync() -> None:
    config = _build_alembic_config()
    command.stamp(config, "head")


async def _detect_schema_state() -> tuple[bool, bool]:
    async with AsyncSessionLocal() as session:
        alembic_table = await session.execute(
            text("SELECT to_regclass('public.alembic_version')")
        )
        core_table = await session.execute(
            text("SELECT to_regclass('public.genres')")
        )
        return bool(alembic_table.scalar()), bool(core_table.scalar())


async def _log_database_event(success: bool, details: str | None = None) -> None:
    try:
        async with AsyncSessionLocal() as session:
            uow = SqlAlchemyUnitOfWork(session)
            service = SystemLogService(uow)
            if success:
                message = "Database migrations completed"
                if details:
                    message = f"{message}: {details}"
                await service.create_log(
                    user_name="*system",
                    severity="INFO",
                    component="Database",
                    message=message,
                )
            else:
                message = "Database migrations failed"
                if details:
                    message = f"{message}: {details}"
                await service.create_log(
                    user_name="*system",
                    severity="ERROR",
                    component="Database",
                    message=message,
                )
    except Exception:
        logger.exception("Failed to log database migration status")


async def run_migrations() -> None:
    try:
        has_alembic, has_schema = await _detect_schema_state()
        if not has_alembic and has_schema:
            await asyncio.to_thread(_stamp_head_sync)
            await _log_database_event(True, "Stamped existing schema")
            return
        await asyncio.to_thread(_run_migrations_sync)
        await _log_database_event(True)
    except Exception as exc:
        await _log_database_event(False, str(exc))
        raise
