"""Lookup tables repository port interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Genre:
    """Genre lookup entity."""
    id: UUID
    name: str
    created_at: datetime
    display_order: Optional[int] = None


@dataclass
class Style:
    """Style lookup entity."""
    id: UUID
    name: str
    created_at: datetime
    genre_id: Optional[UUID] = None
    display_order: Optional[int] = None


@dataclass
class Country:
    """Country lookup entity."""
    code: str  # ISO 3166-1 alpha-2
    name: str
    created_at: datetime
    display_order: Optional[int] = None


@dataclass
class ArtistTypeEntry:
    """Artist type lookup entity."""
    code: str
    name: str
    created_at: datetime
    display_order: Optional[int] = None


@dataclass
class ReleaseTypeEntry:
    """Release type lookup entity."""
    code: str
    name: str
    created_at: datetime
    display_order: Optional[int] = None


@dataclass
class EditionTypeEntry:
    """Edition type lookup entity."""
    code: str
    name: str
    created_at: datetime
    display_order: Optional[int] = None


@dataclass
class SleeveTypeEntry:
    """Sleeve type lookup entity."""
    code: str
    name: str
    created_at: datetime
    display_order: Optional[int] = None


class LookupRepository(ABC):
    """Repository interface for lookup tables (genres, styles, countries)."""

    # ========================================================================
    # GENRES
    # ========================================================================

    @abstractmethod
    async def get_all_genres(self) -> List[Genre]:
        """Get all genres ordered by display_order."""
        pass

    @abstractmethod
    async def get_genre(self, genre_id: UUID) -> Optional[Genre]:
        """Get genre by ID."""
        pass

    @abstractmethod
    async def create_genre(self, name: str, display_order: Optional[int] = None) -> Genre:
        """Create a new genre."""
        pass

    @abstractmethod
    async def update_genre(self, genre_id: UUID, name: str, display_order: Optional[int] = None) -> Genre:
        """Update a genre."""
        pass

    @abstractmethod
    async def delete_genre(self, genre_id: UUID) -> None:
        """Delete a genre (if not in use)."""
        pass

    # ========================================================================
    # STYLES
    # ========================================================================

    @abstractmethod
    async def get_all_styles(self, genre_id: Optional[UUID] = None) -> List[Style]:
        """Get all styles, optionally filtered by genre."""
        pass

    @abstractmethod
    async def get_style(self, style_id: UUID) -> Optional[Style]:
        """Get style by ID."""
        pass

    @abstractmethod
    async def create_style(
        self,
        name: str,
        genre_id: Optional[UUID] = None,
        display_order: Optional[int] = None
    ) -> Style:
        """Create a new style."""
        pass

    @abstractmethod
    async def update_style(
        self,
        style_id: UUID,
        name: str,
        genre_id: Optional[UUID] = None,
        display_order: Optional[int] = None
    ) -> Style:
        """Update a style."""
        pass

    @abstractmethod
    async def delete_style(self, style_id: UUID) -> None:
        """Delete a style (if not in use)."""
        pass

    # ========================================================================
    # COUNTRIES
    # ========================================================================

    @abstractmethod
    async def get_all_countries(self) -> List[Country]:
        """Get all countries ordered by display_order."""
        pass

    @abstractmethod
    async def get_country(self, code: str) -> Optional[Country]:
        """Get country by ISO code."""
        pass

    @abstractmethod
    async def create_country(self, code: str, name: str, display_order: Optional[int] = None) -> Country:
        """Create a new country."""
        pass

    @abstractmethod
    async def update_country(self, code: str, name: str, display_order: Optional[int] = None) -> Country:
        """Update a country."""
        pass

    @abstractmethod
    async def delete_country(self, code: str) -> None:
        """Delete a country (if not in use)."""
        pass

    # ========================================================================
    # ARTIST TYPES
    # ========================================================================

    @abstractmethod
    async def get_all_artist_types(self) -> List[ArtistTypeEntry]:
        """Get all artist types ordered by display_order."""
        pass

    @abstractmethod
    async def get_artist_type(self, code: str) -> Optional[ArtistTypeEntry]:
        """Get artist type by code."""
        pass

    @abstractmethod
    async def create_artist_type(self, code: str, name: str, display_order: Optional[int] = None) -> ArtistTypeEntry:
        """Create a new artist type."""
        pass

    @abstractmethod
    async def update_artist_type(self, code: str, name: str, display_order: Optional[int] = None) -> ArtistTypeEntry:
        """Update an artist type."""
        pass

    @abstractmethod
    async def delete_artist_type(self, code: str) -> None:
        """Delete an artist type (if not in use)."""
        pass

    # ========================================================================
    # RELEASE TYPES
    # ========================================================================

    @abstractmethod
    async def get_all_release_types(self) -> List[ReleaseTypeEntry]:
        """Get all release types ordered by display_order."""
        pass

    @abstractmethod
    async def get_release_type(self, code: str) -> Optional[ReleaseTypeEntry]:
        """Get release type by code."""
        pass

    @abstractmethod
    async def create_release_type(self, code: str, name: str, display_order: Optional[int] = None) -> ReleaseTypeEntry:
        """Create a new release type."""
        pass

    @abstractmethod
    async def update_release_type(self, code: str, name: str, display_order: Optional[int] = None) -> ReleaseTypeEntry:
        """Update a release type."""
        pass

    @abstractmethod
    async def delete_release_type(self, code: str) -> None:
        """Delete a release type (if not in use)."""
        pass

    # ========================================================================
    # EDITION TYPES
    # ========================================================================

    @abstractmethod
    async def get_all_edition_types(self) -> List[EditionTypeEntry]:
        """Get all edition types ordered by display_order."""
        pass

    @abstractmethod
    async def get_edition_type(self, code: str) -> Optional[EditionTypeEntry]:
        """Get edition type by code."""
        pass

    @abstractmethod
    async def create_edition_type(self, code: str, name: str, display_order: Optional[int] = None) -> EditionTypeEntry:
        """Create a new edition type."""
        pass

    @abstractmethod
    async def update_edition_type(self, code: str, name: str, display_order: Optional[int] = None) -> EditionTypeEntry:
        """Update an edition type."""
        pass

    @abstractmethod
    async def delete_edition_type(self, code: str) -> None:
        """Delete an edition type (if not in use)."""
        pass

    # ========================================================================
    # SLEEVE TYPES
    # ========================================================================

    @abstractmethod
    async def get_all_sleeve_types(self) -> List[SleeveTypeEntry]:
        """Get all sleeve types ordered by display_order."""
        pass

    @abstractmethod
    async def get_sleeve_type(self, code: str) -> Optional[SleeveTypeEntry]:
        """Get sleeve type by code."""
        pass

    @abstractmethod
    async def create_sleeve_type(self, code: str, name: str, display_order: Optional[int] = None) -> SleeveTypeEntry:
        """Create a new sleeve type."""
        pass

    @abstractmethod
    async def update_sleeve_type(self, code: str, name: str, display_order: Optional[int] = None) -> SleeveTypeEntry:
        """Update a sleeve type."""
        pass

    @abstractmethod
    async def delete_sleeve_type(self, code: str) -> None:
        """Delete a sleeve type (if not in use)."""
        pass
