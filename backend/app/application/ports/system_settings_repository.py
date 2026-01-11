"""System settings repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities import SystemSetting


class SystemSettingsRepository(ABC):
    """Repository interface for global system settings."""

    @abstractmethod
    async def get(self, key: str) -> Optional[SystemSetting]:
        """Get a system setting by key."""
        raise NotImplementedError

    @abstractmethod
    async def upsert(self, key: str, value: str) -> SystemSetting:
        """Create or update a system setting."""
        raise NotImplementedError
