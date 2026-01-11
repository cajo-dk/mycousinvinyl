"""System log repository PostgreSQL adapter."""

from datetime import datetime
from typing import List, Tuple

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.system_log_repository import SystemLogRepository
from app.adapters.postgres.models import SystemLogModel
from app.domain.entities import SystemLogEntry


class SystemLogRepositoryAdapter(SystemLogRepository):
    """PostgreSQL implementation of SystemLogRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entry: SystemLogEntry) -> SystemLogEntry:
        model = SystemLogModel.from_domain(entry)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def list(self, limit: int, offset: int) -> Tuple[List[SystemLogEntry], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(SystemLogModel)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(SystemLogModel)
            .order_by(SystemLogModel.created_at.desc(), SystemLogModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models], total

    async def delete_older_than(self, cutoff: datetime) -> int:
        result = await self.session.execute(
            delete(SystemLogModel).where(SystemLogModel.created_at < cutoff)
        )
        await self.session.flush()
        return result.rowcount or 0
