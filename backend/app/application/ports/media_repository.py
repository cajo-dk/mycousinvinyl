"""Media asset repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.entities import MediaAsset


class MediaRepository(ABC):
    """Repository interface for MediaAsset entities."""

    @abstractmethod
    async def add(self, media: MediaAsset) -> MediaAsset:
        """Add a new media asset."""
        pass

    @abstractmethod
    async def get(self, media_id: UUID) -> Optional[MediaAsset]:
        """Get media asset by ID."""
        pass

    @abstractmethod
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID
    ) -> List[MediaAsset]:
        """Get all media assets for an entity."""
        pass

    @abstractmethod
    async def update(self, media: MediaAsset) -> MediaAsset:
        """Update media asset."""
        pass

    @abstractmethod
    async def delete(self, media_id: UUID) -> None:
        """Delete media asset."""
        pass
