"""Pressing repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID

from app.domain.entities import Pressing


class PressingRepository(ABC):
    """Repository interface for Pressing entities."""

    @abstractmethod
    async def add(self, pressing: Pressing) -> Pressing:
        """Add a new pressing."""
        pass

    @abstractmethod
    async def get(self, pressing_id: UUID) -> Optional[Pressing]:
        """Get pressing by ID."""
        pass

    @abstractmethod
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Pressing], int]:
        """
        Get all pressings with optional filters.

        Filters:
            - format: VinylFormat
            - speed: VinylSpeed
            - size: VinylSize
            - country: str - Pressing country
            - year_min: int - Minimum pressing year
            - year_max: int - Maximum pressing year

        Returns:
            Tuple of (pressings list, total count)
        """
        pass

    @abstractmethod
    async def get_by_album(
        self,
        album_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Pressing], int]:
        """Get all pressings for an album."""
        pass

    @abstractmethod
    async def update(self, pressing: Pressing) -> Pressing:
        """Update an existing pressing."""
        pass

    @abstractmethod
    async def delete(self, pressing_id: UUID) -> None:
        """Delete a pressing."""
        pass

    @abstractmethod
    async def exists(self, pressing_id: UUID) -> bool:
        """Check if pressing exists."""
        pass

    @abstractmethod
    async def is_in_collections(self, pressing_id: UUID) -> bool:
        """Check if pressing is in any user collections."""
        pass

    @abstractmethod
    async def has_children(self, pressing_id: UUID) -> bool:
        """Check if pressing has child pressings (is a master)."""
        pass

    @abstractmethod
    async def get_master_by_discogs_id(self, discogs_master_id: int) -> Optional[Pressing]:
        """Get master pressing by Discogs master ID."""
        pass

    @abstractmethod
    async def get_by_discogs_release_id(self, discogs_release_id: int) -> Optional[Pressing]:
        """Get pressing by Discogs release ID."""
        pass
