"""
Lookup service for managing genres, styles, and countries.

Admin-focused service for maintaining reference data.
Security-agnostic - authorization enforced at HTTP entrypoint layer.
"""

from uuid import UUID
from typing import List, Optional

from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.lookup_repository import (
    Genre, Style, Country,
    ArtistTypeEntry, ReleaseTypeEntry, EditionTypeEntry, SleeveTypeEntry
)


class LookupService:
    """Service for managing lookup/reference data."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ========================================================================
    # GENRES
    # ========================================================================

    async def get_all_genres(self) -> List[Genre]:
        """Get all genres ordered by display_order."""
        async with self.uow:
            return await self.uow.lookup_repository.get_all_genres()

    async def get_genre(self, genre_id: UUID) -> Optional[Genre]:
        """Get genre by ID."""
        async with self.uow:
            return await self.uow.lookup_repository.get_genre(genre_id)

    async def create_genre(
        self,
        name: str,
        display_order: Optional[int] = None
    ) -> Genre:
        """Create a new genre."""
        async with self.uow:
            result = await self.uow.lookup_repository.create_genre(name, display_order)
            await self.uow.commit()
        return result

    async def update_genre(
        self,
        genre_id: UUID,
        name: str,
        display_order: Optional[int] = None
    ) -> Genre:
        """Update a genre."""
        async with self.uow:
            result = await self.uow.lookup_repository.update_genre(genre_id, name, display_order)
            await self.uow.commit()
        return result

    async def delete_genre(self, genre_id: UUID) -> bool:
        """
        Delete a genre.

        Note: Will fail if genre is in use by albums (database constraint).
        """
        try:
            async with self.uow:
                await self.uow.lookup_repository.delete_genre(genre_id)
                await self.uow.commit()
            return True
        except Exception:
            return False

    # ========================================================================
    # STYLES
    # ========================================================================

    async def get_all_styles(self, genre_id: Optional[UUID] = None) -> List[Style]:
        """Get all styles, optionally filtered by genre."""
        async with self.uow:
            return await self.uow.lookup_repository.get_all_styles(genre_id)

    async def get_style(self, style_id: UUID) -> Optional[Style]:
        """Get style by ID."""
        async with self.uow:
            return await self.uow.lookup_repository.get_style(style_id)

    async def create_style(
        self,
        name: str,
        genre_id: Optional[UUID] = None,
        display_order: Optional[int] = None
    ) -> Style:
        """Create a new style."""
        async with self.uow:
            result = await self.uow.lookup_repository.create_style(name, genre_id, display_order)
            await self.uow.commit()
        return result

    async def update_style(
        self,
        style_id: UUID,
        name: str,
        genre_id: Optional[UUID] = None,
        display_order: Optional[int] = None
    ) -> Style:
        """Update a style."""
        async with self.uow:
            result = await self.uow.lookup_repository.update_style(
                style_id, name, genre_id, display_order
            )
            await self.uow.commit()
        return result

    async def delete_style(self, style_id: UUID) -> bool:
        """
        Delete a style.

        Note: Will fail if style is in use by albums (database constraint).
        """
        try:
            async with self.uow:
                await self.uow.lookup_repository.delete_style(style_id)
                await self.uow.commit()
            return True
        except Exception:
            return False

    # ========================================================================
    # COUNTRIES
    # ========================================================================

    async def get_all_countries(self) -> List[Country]:
        """Get all countries ordered by display_order."""
        async with self.uow:
            return await self.uow.lookup_repository.get_all_countries()

    async def get_country(self, code: str) -> Optional[Country]:
        """Get country by ISO code."""
        async with self.uow:
            return await self.uow.lookup_repository.get_country(code)

    async def create_country(
        self,
        code: str,
        name: str,
        display_order: Optional[int] = None
    ) -> Country:
        """Create a new country."""
        async with self.uow:
            result = await self.uow.lookup_repository.create_country(code, name, display_order)
            await self.uow.commit()
        return result

    async def update_country(
        self,
        code: str,
        name: str,
        display_order: Optional[int] = None
    ) -> Country:
        """Update a country."""
        async with self.uow:
            result = await self.uow.lookup_repository.update_country(code, name, display_order)
            await self.uow.commit()
        return result

    async def delete_country(self, code: str) -> bool:
        """
        Delete a country.

        Note: Will fail if country is in use (database constraint).
        """
        try:
            async with self.uow:
                await self.uow.lookup_repository.delete_country(code)
                await self.uow.commit()
            return True
        except Exception:
            return False

    # ========================================================================
    # ARTIST TYPES
    # ========================================================================

    async def get_all_artist_types(self) -> List[ArtistTypeEntry]:
        """Get all artist types ordered by display_order."""
        async with self.uow:
            return await self.uow.lookup_repository.get_all_artist_types()

    async def get_artist_type(self, code: str) -> Optional[ArtistTypeEntry]:
        """Get artist type by code."""
        async with self.uow:
            return await self.uow.lookup_repository.get_artist_type(code)

    async def create_artist_type(
        self,
        code: str,
        name: str,
        display_order: Optional[int] = None
    ) -> ArtistTypeEntry:
        """Create a new artist type."""
        async with self.uow:
            result = await self.uow.lookup_repository.create_artist_type(code, name, display_order)
            await self.uow.commit()
        return result

    async def update_artist_type(
        self,
        code: str,
        name: str,
        display_order: Optional[int] = None
    ) -> ArtistTypeEntry:
        """Update an artist type."""
        async with self.uow:
            result = await self.uow.lookup_repository.update_artist_type(code, name, display_order)
            await self.uow.commit()
        return result

    async def delete_artist_type(self, code: str) -> bool:
        """Delete an artist type (if not in use)."""
        try:
            async with self.uow:
                await self.uow.lookup_repository.delete_artist_type(code)
                await self.uow.commit()
            return True
        except Exception:
            return False

    # ========================================================================
    # RELEASE TYPES
    # ========================================================================

    async def get_all_release_types(self) -> List[ReleaseTypeEntry]:
        """Get all release types ordered by display_order."""
        async with self.uow:
            return await self.uow.lookup_repository.get_all_release_types()

    async def get_release_type(self, code: str) -> Optional[ReleaseTypeEntry]:
        """Get release type by code."""
        async with self.uow:
            return await self.uow.lookup_repository.get_release_type(code)

    async def create_release_type(
        self,
        code: str,
        name: str,
        display_order: Optional[int] = None
    ) -> ReleaseTypeEntry:
        """Create a new release type."""
        async with self.uow:
            result = await self.uow.lookup_repository.create_release_type(code, name, display_order)
            await self.uow.commit()
        return result

    async def update_release_type(
        self,
        code: str,
        name: str,
        display_order: Optional[int] = None
    ) -> ReleaseTypeEntry:
        """Update a release type."""
        async with self.uow:
            result = await self.uow.lookup_repository.update_release_type(code, name, display_order)
            await self.uow.commit()
        return result

    async def delete_release_type(self, code: str) -> bool:
        """Delete a release type (if not in use)."""
        try:
            async with self.uow:
                await self.uow.lookup_repository.delete_release_type(code)
                await self.uow.commit()
            return True
        except Exception:
            return False

    # ========================================================================
    # EDITION TYPES
    # ========================================================================

    async def get_all_edition_types(self) -> List[EditionTypeEntry]:
        """Get all edition types ordered by display_order."""
        async with self.uow:
            return await self.uow.lookup_repository.get_all_edition_types()

    async def get_edition_type(self, code: str) -> Optional[EditionTypeEntry]:
        """Get edition type by code."""
        async with self.uow:
            return await self.uow.lookup_repository.get_edition_type(code)

    async def create_edition_type(
        self,
        code: str,
        name: str,
        display_order: Optional[int] = None
    ) -> EditionTypeEntry:
        """Create a new edition type."""
        async with self.uow:
            result = await self.uow.lookup_repository.create_edition_type(code, name, display_order)
            await self.uow.commit()
        return result

    async def update_edition_type(
        self,
        code: str,
        name: str,
        display_order: Optional[int] = None
    ) -> EditionTypeEntry:
        """Update an edition type."""
        async with self.uow:
            result = await self.uow.lookup_repository.update_edition_type(code, name, display_order)
            await self.uow.commit()
        return result

    async def delete_edition_type(self, code: str) -> bool:
        """Delete an edition type (if not in use)."""
        try:
            async with self.uow:
                await self.uow.lookup_repository.delete_edition_type(code)
                await self.uow.commit()
            return True
        except Exception:
            return False

    # ========================================================================
    # SLEEVE TYPES
    # ========================================================================

    async def get_all_sleeve_types(self) -> List[SleeveTypeEntry]:
        """Get all sleeve types ordered by display_order."""
        async with self.uow:
            return await self.uow.lookup_repository.get_all_sleeve_types()

    async def get_sleeve_type(self, code: str) -> Optional[SleeveTypeEntry]:
        """Get sleeve type by code."""
        async with self.uow:
            return await self.uow.lookup_repository.get_sleeve_type(code)

    async def create_sleeve_type(
        self,
        code: str,
        name: str,
        display_order: Optional[int] = None
    ) -> SleeveTypeEntry:
        """Create a new sleeve type."""
        async with self.uow:
            result = await self.uow.lookup_repository.create_sleeve_type(code, name, display_order)
            await self.uow.commit()
        return result

    async def update_sleeve_type(
        self,
        code: str,
        name: str,
        display_order: Optional[int] = None
    ) -> SleeveTypeEntry:
        """Update a sleeve type."""
        async with self.uow:
            result = await self.uow.lookup_repository.update_sleeve_type(code, name, display_order)
            await self.uow.commit()
        return result

    async def delete_sleeve_type(self, code: str) -> bool:
        """Delete a sleeve type (if not in use)."""
        try:
            async with self.uow:
                await self.uow.lookup_repository.delete_sleeve_type(code)
                await self.uow.commit()
            return True
        except Exception:
            return False
