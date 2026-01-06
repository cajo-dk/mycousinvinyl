"""User preferences repository port interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from app.domain.entities import UserPreferences


class PreferencesRepository(ABC):
    """Repository interface for UserPreferences entities."""

    @abstractmethod
    async def get(self, user_id: UUID) -> Optional[UserPreferences]:
        """Get user preferences by user ID."""
        pass

    @abstractmethod
    async def create(self, preferences: UserPreferences) -> UserPreferences:
        """Create user preferences."""
        pass

    @abstractmethod
    async def update(self, preferences: UserPreferences) -> UserPreferences:
        """Update user preferences."""
        pass

    @abstractmethod
    async def get_or_create_default(self, user_id: UUID) -> UserPreferences:
        """Get user preferences or create with defaults if not exists."""
        pass

    @abstractmethod
    async def get_many_by_user_ids(self, user_ids: List[UUID]) -> Dict[UUID, UserPreferences]:
        """
        Get multiple user preferences by list of user IDs.

        Args:
            user_ids: List of user IDs to retrieve preferences for

        Returns:
            Dictionary mapping user_id to UserPreferences (only includes found users)
        """
        pass

    @abstractmethod
    async def search_users_by_name(self, query: str, limit: int = 10) -> List[UserPreferences]:
        """
        Search for users by name (for autocomplete in user search).

        Searches in user_profile.display_name and user_profile.first_name fields
        stored in display_settings JSONB. Only returns users with collection
        sharing enabled.

        Args:
            query: Search query string (case-insensitive partial match)
            limit: Maximum number of results to return (default 10)

        Returns:
            List of UserPreferences for matching users with sharing enabled
        """
        pass
