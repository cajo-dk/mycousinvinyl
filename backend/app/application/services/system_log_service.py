"""System log application service."""

from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from uuid import UUID

from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities import SystemLogEntry


class SystemLogService:
    """Service for managing system audit logs and retention."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_log(
        self,
        user_name: str,
        severity: str,
        component: str,
        message: str,
        user_id: Optional[UUID] = None,
    ) -> SystemLogEntry:
        severity_value = severity.upper()
        if severity_value not in {"INFO", "WARN", "ERROR"}:
            raise ValueError("Invalid log severity")

        entry = SystemLogEntry(
            user_id=user_id,
            user_name=user_name,
            severity=severity_value,
            component=component,
            message=message,
        )
        async with self.uow:
            created = await self.uow.system_log_repository.create(entry)
            await self.uow.commit()
            return created

    async def list_logs(self, limit: int, offset: int) -> Tuple[List[SystemLogEntry], int]:
        async with self.uow:
            return await self.uow.system_log_repository.list(limit=limit, offset=offset)

    async def _get_retention_days(self) -> int:
        setting = await self.uow.system_settings_repository.get("log_retention_days")
        if not setting or not setting.value:
            return 60
        try:
            return int(setting.value)
        except ValueError:
            return 60

    async def get_retention_days(self) -> int:
        async with self.uow:
            return await self._get_retention_days()

    async def set_retention_days(self, days: int) -> int:
        if days not in {30, 60, 90}:
            raise ValueError("Retention must be 30, 60, or 90 days")
        async with self.uow:
            await self.uow.system_settings_repository.upsert(
                key="log_retention_days",
                value=str(days)
            )
            await self.uow.commit()
            return days

    async def prune_logs(self) -> int:
        async with self.uow:
            retention_days = await self._get_retention_days()
            cutoff = datetime.utcnow() - timedelta(days=retention_days)
            deleted = await self.uow.system_log_repository.delete_older_than(cutoff)
            await self.uow.commit()
            return deleted
