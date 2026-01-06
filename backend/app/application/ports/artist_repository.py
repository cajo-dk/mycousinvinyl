"""Artist repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from uuid import UUID

from app.domain.entities import Artist


class ArtistRepository(ABC):
    """Repository interface for Artist entities."""

    @abstractmethod
    async def add(self, artist: Artist) -> Artist:
        """Add a new artist."""
        pass

    @abstractmethod
    async def get(self, artist_id: UUID) -> Optional[Artist]:
        """Get artist by ID."""
        pass

    @abstractmethod
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "name",
        artist_type: Optional[str] = None,
        country: Optional[str] = None
    ) -> Tuple[List[Artist], int]:
        """
        Get all artists with pagination.

        Returns:
            Tuple of (artists list, total count)
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        artist_type: Optional[str] = None,
        country: Optional[str] = None
    ) -> Tuple[List[Artist], int]:
        """
        Search artists by name (fuzzy search).

        Returns:
            Tuple of (artists list, total count)
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Artist]:
        """Get artist by exact name match."""
        pass

    @abstractmethod
    async def get_by_discogs_id(self, discogs_id: int) -> Optional[Artist]:
        """Get artist by Discogs ID."""
        pass

    @abstractmethod
    async def update(self, artist: Artist) -> Artist:
        """Update an existing artist."""
        pass

    @abstractmethod
    async def delete(self, artist_id: UUID) -> None:
        """Delete an artist."""
        pass

    @abstractmethod
    async def exists(self, artist_id: UUID) -> bool:
        """Check if artist exists."""
        pass
