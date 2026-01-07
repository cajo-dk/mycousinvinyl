"""Lookup repository PostgreSQL adapter."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.lookup_repository import (
    LookupRepository, Genre, Style, Country,
    ArtistTypeEntry, ReleaseTypeEntry, EditionTypeEntry, SleeveTypeEntry
)
from app.adapters.postgres.models import (
    GenreModel, StyleModel, CountryModel,
    ArtistTypeModel, ReleaseTypeModel, EditionTypeModel, SleeveTypeModel
)


class LookupRepositoryAdapter(LookupRepository):
    """PostgreSQL implementation of LookupRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================================================
    # GENRES
    # ========================================================================

    async def get_all_genres(self) -> List[Genre]:
        """Get all genres ordered by display_order."""
        result = await self.session.execute(
            select(GenreModel).order_by(GenreModel.display_order.nullslast(), GenreModel.name)
        )
        models = result.scalars().all()
        return [
            Genre(id=m.id, name=m.name, created_at=m.created_at, display_order=m.display_order)
            for m in models
        ]

    async def get_genre(self, genre_id: UUID) -> Optional[Genre]:
        """Get genre by ID."""
        result = await self.session.execute(
            select(GenreModel).where(GenreModel.id == genre_id)
        )
        model = result.scalar_one_or_none()
        return Genre(id=model.id, name=model.name, created_at=model.created_at, display_order=model.display_order) if model else None

    async def create_genre(self, name: str, display_order: Optional[int] = None) -> Genre:
        """Create a new genre."""
        model = GenreModel(name=name, display_order=display_order)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return Genre(id=model.id, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def update_genre(self, genre_id: UUID, name: str, display_order: Optional[int] = None) -> Genre:
        """Update a genre."""
        result = await self.session.execute(
            select(GenreModel).where(GenreModel.id == genre_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Genre {genre_id} not found")

        model.name = name
        model.display_order = display_order

        await self.session.flush()
        await self.session.refresh(model)
        return Genre(id=model.id, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def delete_genre(self, genre_id: UUID) -> None:
        """Delete a genre (if not in use)."""
        await self.session.execute(
            delete(GenreModel).where(GenreModel.id == genre_id)
        )
        await self.session.flush()

    # ========================================================================
    # STYLES
    # ========================================================================

    async def get_all_styles(self, genre_id: Optional[UUID] = None) -> List[Style]:
        """Get all styles, optionally filtered by genre."""
        query = select(StyleModel)

        if genre_id:
            query = query.where(StyleModel.genre_id == genre_id)

        query = query.order_by(StyleModel.display_order.nullslast(), StyleModel.name)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [
            Style(
                id=m.id,
                name=m.name,
                created_at=m.created_at,
                genre_id=m.genre_id,
                display_order=m.display_order
            )
            for m in models
        ]

    async def get_style(self, style_id: UUID) -> Optional[Style]:
        """Get style by ID."""
        result = await self.session.execute(
            select(StyleModel).where(StyleModel.id == style_id)
        )
        model = result.scalar_one_or_none()
        return Style(
            id=model.id,
            name=model.name,
            created_at=model.created_at,
            genre_id=model.genre_id,
            display_order=model.display_order
        ) if model else None

    async def create_style(
        self,
        name: str,
        genre_id: Optional[UUID] = None,
        display_order: Optional[int] = None
    ) -> Style:
        """Create a new style."""
        model = StyleModel(name=name, genre_id=genre_id, display_order=display_order)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return Style(
            id=model.id,
            name=model.name,
            created_at=model.created_at,
            genre_id=model.genre_id,
            display_order=model.display_order
        )

    async def update_style(
        self,
        style_id: UUID,
        name: str,
        genre_id: Optional[UUID] = None,
        display_order: Optional[int] = None
    ) -> Style:
        """Update a style."""
        result = await self.session.execute(
            select(StyleModel).where(StyleModel.id == style_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Style {style_id} not found")

        model.name = name
        model.genre_id = genre_id
        model.display_order = display_order

        await self.session.flush()
        await self.session.refresh(model)
        return Style(
            id=model.id,
            name=model.name,
            created_at=model.created_at,
            genre_id=model.genre_id,
            display_order=model.display_order
        )

    async def delete_style(self, style_id: UUID) -> None:
        """Delete a style (if not in use)."""
        await self.session.execute(
            delete(StyleModel).where(StyleModel.id == style_id)
        )
        await self.session.flush()

    # ========================================================================
    # COUNTRIES
    # ========================================================================

    async def get_all_countries(self) -> List[Country]:
        """Get all countries ordered by display_order."""
        result = await self.session.execute(
            select(CountryModel).order_by(CountryModel.display_order.nullslast(), CountryModel.name)
        )
        models = result.scalars().all()
        return [
            Country(code=m.code, name=m.name, created_at=m.created_at, display_order=m.display_order)
            for m in models
        ]

    async def get_country(self, code: str) -> Optional[Country]:
        """Get country by ISO code."""
        result = await self.session.execute(
            select(CountryModel).where(CountryModel.code == code)
        )
        model = result.scalar_one_or_none()
        return Country(
            code=model.code,
            name=model.name,
            created_at=model.created_at,
            display_order=model.display_order
        ) if model else None

    async def create_country(self, code: str, name: str, display_order: Optional[int] = None) -> Country:
        """Create a new country."""
        model = CountryModel(code=code, name=name, display_order=display_order)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return Country(code=model.code, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def update_country(self, code: str, name: str, display_order: Optional[int] = None) -> Country:
        """Update a country."""
        result = await self.session.execute(
            select(CountryModel).where(CountryModel.code == code)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Country {code} not found")

        model.name = name
        model.display_order = display_order

        await self.session.flush()
        await self.session.refresh(model)
        return Country(code=model.code, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def delete_country(self, code: str) -> None:
        """Delete a country (if not in use)."""
        await self.session.execute(
            delete(CountryModel).where(CountryModel.code == code)
        )
        await self.session.flush()

    # ========================================================================
    # ARTIST TYPES
    # ========================================================================

    async def get_all_artist_types(self) -> List[ArtistTypeEntry]:
        """Get all artist types ordered by display_order."""
        result = await self.session.execute(
            select(ArtistTypeModel).order_by(ArtistTypeModel.display_order.nullslast(), ArtistTypeModel.name)
        )
        models = result.scalars().all()
        return [
            ArtistTypeEntry(code=m.code, name=m.name, created_at=m.created_at, display_order=m.display_order)
            for m in models
        ]

    async def get_artist_type(self, code: str) -> Optional[ArtistTypeEntry]:
        """Get artist type by code."""
        result = await self.session.execute(
            select(ArtistTypeModel).where(ArtistTypeModel.code == code)
        )
        model = result.scalar_one_or_none()
        return ArtistTypeEntry(
            code=model.code,
            name=model.name,
            created_at=model.created_at,
            display_order=model.display_order
        ) if model else None

    async def create_artist_type(self, code: str, name: str, display_order: Optional[int] = None) -> ArtistTypeEntry:
        """Create a new artist type."""
        model = ArtistTypeModel(code=code, name=name, display_order=display_order)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return ArtistTypeEntry(code=model.code, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def update_artist_type(self, code: str, name: str, display_order: Optional[int] = None) -> ArtistTypeEntry:
        """Update an artist type."""
        result = await self.session.execute(
            select(ArtistTypeModel).where(ArtistTypeModel.code == code)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Artist type {code} not found")

        model.name = name
        model.display_order = display_order

        await self.session.flush()
        await self.session.refresh(model)
        return ArtistTypeEntry(code=model.code, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def delete_artist_type(self, code: str) -> None:
        """Delete an artist type (if not in use)."""
        await self.session.execute(
            delete(ArtistTypeModel).where(ArtistTypeModel.code == code)
        )
        await self.session.flush()

    # ========================================================================
    # RELEASE TYPES
    # ========================================================================

    async def get_all_release_types(self) -> List[ReleaseTypeEntry]:
        """Get all release types ordered by display_order."""
        result = await self.session.execute(
            select(ReleaseTypeModel).order_by(ReleaseTypeModel.display_order.nullslast(), ReleaseTypeModel.name)
        )
        models = result.scalars().all()
        return [
            ReleaseTypeEntry(code=m.code, name=m.name, created_at=m.created_at, display_order=m.display_order)
            for m in models
        ]

    async def get_release_type(self, code: str) -> Optional[ReleaseTypeEntry]:
        """Get release type by code."""
        result = await self.session.execute(
            select(ReleaseTypeModel).where(ReleaseTypeModel.code == code)
        )
        model = result.scalar_one_or_none()
        return ReleaseTypeEntry(
            code=model.code,
            name=model.name,
            created_at=model.created_at,
            display_order=model.display_order
        ) if model else None

    async def create_release_type(self, code: str, name: str, display_order: Optional[int] = None) -> ReleaseTypeEntry:
        """Create a new release type."""
        model = ReleaseTypeModel(code=code, name=name, display_order=display_order)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return ReleaseTypeEntry(code=model.code, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def update_release_type(self, code: str, name: str, display_order: Optional[int] = None) -> ReleaseTypeEntry:
        """Update a release type."""
        result = await self.session.execute(
            select(ReleaseTypeModel).where(ReleaseTypeModel.code == code)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Release type {code} not found")

        model.name = name
        model.display_order = display_order

        await self.session.flush()
        await self.session.refresh(model)
        return ReleaseTypeEntry(code=model.code, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def delete_release_type(self, code: str) -> None:
        """Delete a release type (if not in use)."""
        await self.session.execute(
            delete(ReleaseTypeModel).where(ReleaseTypeModel.code == code)
        )
        await self.session.flush()

    # ========================================================================
    # EDITION TYPES
    # ========================================================================

    async def get_all_edition_types(self) -> List[EditionTypeEntry]:
        """Get all edition types ordered by display_order."""
        result = await self.session.execute(
            select(EditionTypeModel).order_by(EditionTypeModel.display_order.nullslast(), EditionTypeModel.name)
        )
        models = result.scalars().all()
        return [
            EditionTypeEntry(code=m.code, name=m.name, created_at=m.created_at, display_order=m.display_order)
            for m in models
        ]

    async def get_edition_type(self, code: str) -> Optional[EditionTypeEntry]:
        """Get edition type by code."""
        result = await self.session.execute(
            select(EditionTypeModel).where(EditionTypeModel.code == code)
        )
        model = result.scalar_one_or_none()
        return EditionTypeEntry(
            code=model.code,
            name=model.name,
            created_at=model.created_at,
            display_order=model.display_order
        ) if model else None

    async def create_edition_type(self, code: str, name: str, display_order: Optional[int] = None) -> EditionTypeEntry:
        """Create a new edition type."""
        model = EditionTypeModel(code=code, name=name, display_order=display_order)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return EditionTypeEntry(code=model.code, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def update_edition_type(self, code: str, name: str, display_order: Optional[int] = None) -> EditionTypeEntry:
        """Update an edition type."""
        result = await self.session.execute(
            select(EditionTypeModel).where(EditionTypeModel.code == code)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Edition type {code} not found")

        model.name = name
        model.display_order = display_order

        await self.session.flush()
        await self.session.refresh(model)
        return EditionTypeEntry(code=model.code, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def delete_edition_type(self, code: str) -> None:
        """Delete an edition type (if not in use)."""
        await self.session.execute(
            delete(EditionTypeModel).where(EditionTypeModel.code == code)
        )
        await self.session.flush()

    # ========================================================================
    # SLEEVE TYPES
    # ========================================================================

    async def get_all_sleeve_types(self) -> List[SleeveTypeEntry]:
        """Get all sleeve types ordered by display_order."""
        result = await self.session.execute(
            select(SleeveTypeModel).order_by(SleeveTypeModel.display_order.nullslast(), SleeveTypeModel.name)
        )
        models = result.scalars().all()
        return [
            SleeveTypeEntry(code=m.code, name=m.name, created_at=m.created_at, display_order=m.display_order)
            for m in models
        ]

    async def get_sleeve_type(self, code: str) -> Optional[SleeveTypeEntry]:
        """Get sleeve type by code."""
        result = await self.session.execute(
            select(SleeveTypeModel).where(SleeveTypeModel.code == code)
        )
        model = result.scalar_one_or_none()
        return SleeveTypeEntry(
            code=model.code,
            name=model.name,
            created_at=model.created_at,
            display_order=model.display_order
        ) if model else None

    async def create_sleeve_type(self, code: str, name: str, display_order: Optional[int] = None) -> SleeveTypeEntry:
        """Create a new sleeve type."""
        model = SleeveTypeModel(code=code, name=name, display_order=display_order)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return SleeveTypeEntry(code=model.code, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def update_sleeve_type(self, code: str, name: str, display_order: Optional[int] = None) -> SleeveTypeEntry:
        """Update a sleeve type."""
        result = await self.session.execute(
            select(SleeveTypeModel).where(SleeveTypeModel.code == code)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Sleeve type {code} not found")

        model.name = name
        model.display_order = display_order

        await self.session.flush()
        await self.session.refresh(model)
        return SleeveTypeEntry(code=model.code, name=model.name, created_at=model.created_at, display_order=model.display_order)

    async def delete_sleeve_type(self, code: str) -> None:
        """Delete a sleeve type (if not in use)."""
        await self.session.execute(
            delete(SleeveTypeModel).where(SleeveTypeModel.code == code)
        )
        await self.session.flush()
