"""System settings repository PostgreSQL adapter."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.system_settings_repository import SystemSettingsRepository
from app.adapters.postgres.models import SystemSettingModel
from app.domain.entities import SystemSetting


class SystemSettingsRepositoryAdapter(SystemSettingsRepository):
    """PostgreSQL implementation of SystemSettingsRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> Optional[SystemSetting]:
        result = await self.session.execute(
            select(SystemSettingModel).where(SystemSettingModel.key == key)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def upsert(self, key: str, value: str) -> SystemSetting:
        stmt = insert(SystemSettingModel).values(
            key=key,
            value=value,
        ).on_conflict_do_update(
            index_elements=[SystemSettingModel.key],
            set_={"value": value}
        ).returning(SystemSettingModel)

        result = await self.session.execute(stmt)
        model = result.scalar_one()
        await self.session.flush()
        return model.to_domain()
