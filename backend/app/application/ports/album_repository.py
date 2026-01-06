"""Album repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID

from app.domain.entities import Album


class AlbumRepository(ABC):
    """Repository interface for Album entities."""

    @abstractmethod
    async def add(self, album: Album) -> Album:
        """Add a new album."""
        pass

    @abstractmethod
    async def get(self, album_id: UUID) -> Optional[Album]:
        """Get album by ID with genres and styles."""
        pass

    @abstractmethod
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "title"
    ) -> Tuple[List[Album], int]:
        """
        Get all albums with pagination.

        Returns:
            Tuple of (albums list, total count)
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "relevance",
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Album], int]:
        """
        Search albums with full-text search and filters.

        Filters:
            - genres: List[UUID] - Filter by genre IDs (OR within, AND across)
            - styles: List[UUID] - Filter by style IDs
            - year_min: int - Minimum release year
            - year_max: int - Maximum release year
            - artist_id: UUID - Filter by primary artist
            - release_type: str - Filter by release type
            - country: str - Filter by country of origin

        Returns:
            Tuple of (albums list, total count)
        """
        pass

    @abstractmethod
    async def get_by_artist(
        self,
        artist_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Album], int]:
        """Get all albums by an artist."""
        pass

    @abstractmethod
    async def get_by_discogs_id(self, discogs_id: int) -> Optional[Album]:
        """Get album by Discogs ID."""
        pass

    @abstractmethod
    async def get_by_title_and_artist(self, artist_id: UUID, title: str) -> Optional[Album]:
        """Get album by exact title match for a given artist."""
        pass

    @abstractmethod
    async def search_by_title_and_artist(
        self,
        artist_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Album]:
        """Search albums by title for a given artist (partial match)."""
        pass

    @abstractmethod
    async def get_all_with_details(
        self,
        query: Optional[str] = None,
        artist_id: Optional[UUID] = None,
        genre_ids: Optional[List[UUID]] = None,
        style_ids: Optional[List[UUID]] = None,
        release_type: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get albums with artist details, pressing counts, and optional filters."""
        pass

    @abstractmethod
    async def update(self, album: Album) -> Album:
        """Update an existing album."""
        pass

    @abstractmethod
    async def delete(self, album_id: UUID) -> None:
        """Delete an album."""
        pass

    @abstractmethod
    async def exists(self, album_id: UUID) -> bool:
        """Check if album exists."""
        pass

    @abstractmethod
    async def has_pressings(self, album_id: UUID) -> bool:
        """Check if album has any pressings."""
        pass
