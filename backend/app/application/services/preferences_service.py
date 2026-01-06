"""
User preferences application service.

Manages user-specific settings.
Security-agnostic - user_id provided from authenticated context at HTTP layer.
"""

from uuid import UUID
from typing import Optional, Dict, Any

from app.domain.entities import UserPreferences
from app.application.ports.unit_of_work import UnitOfWork


class PreferencesService:
    """Service for user preferences management."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_user_preferences(self, user_id: UUID) -> UserPreferences:
        """
        Get user preferences.

        Creates default preferences if none exist (get-or-create pattern).
        """
        async with self.uow:
            return await self.uow.preferences_repository.get_or_create_default(user_id)

    async def update_currency(
        self,
        user_id: UUID,
        currency: str
    ) -> UserPreferences:
        """
        Update user's preferred currency.

        Validates currency code (3-letter ISO 4217).
        """
        async with self.uow:
            prefs = await self.uow.preferences_repository.get_or_create_default(user_id)

            # Use domain entity business method (validates currency)
            prefs.update_currency(currency)

            result = await self.uow.preferences_repository.update(prefs)
            await self.uow.commit()

        return result

    async def update_display_settings(
        self,
        user_id: UUID,
        settings: Dict[str, Any]
    ) -> UserPreferences:
        """
        Update user's display settings.

        Settings stored as JSONB, allowing flexible key-value pairs.
        """
        async with self.uow:
            prefs = await self.uow.preferences_repository.get_or_create_default(user_id)

            # Use domain entity business method
            prefs.update_display_settings(settings)

            result = await self.uow.preferences_repository.update(prefs)
            await self.uow.commit()

        return result

    async def update_preferences(
        self,
        user_id: UUID,
        currency: Optional[str] = None,
        display_settings: Optional[Dict[str, Any]] = None
    ) -> UserPreferences:
        """
        Update user preferences (currency and/or display settings).

        Convenience method for updating multiple preferences at once.
        """
        async with self.uow:
            prefs = await self.uow.preferences_repository.get_or_create_default(user_id)

            if currency:
                prefs.update_currency(currency)

            if display_settings:
                prefs.update_display_settings(display_settings)

            result = await self.uow.preferences_repository.update(prefs)
            await self.uow.commit()

        return result
