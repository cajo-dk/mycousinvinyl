"""Artist repository PostgreSQL adapter."""

from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.artist_repository import ArtistRepository
from app.domain.entities import Artist
from app.adapters.postgres.models import ArtistModel, AlbumModel, _build_active_years


class ArtistRepositoryAdapter(ArtistRepository):
    """PostgreSQL implementation of ArtistRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _apply_album_counts(self, artists: List[Artist]) -> None:
        if not artists:
            return

        artist_ids = [artist.id for artist in artists]
        count_query = (
            select(AlbumModel.primary_artist_id, func.count(AlbumModel.id))
            .where(AlbumModel.primary_artist_id.in_(artist_ids))
            .group_by(AlbumModel.primary_artist_id)
        )
        result = await self.session.execute(count_query)
        counts = {row[0]: row[1] for row in result.all()}

        for artist in artists:
            artist.album_count = counts.get(artist.id, 0)

    def _apply_filters(self, query, artist_type: Optional[str], country: Optional[str]):
        if artist_type:
            query = query.where(ArtistModel.type == artist_type)
        if country:
            query = query.where(ArtistModel.country == country)
        return query

    async def add(self, artist: Artist) -> Artist:
        """Add a new artist."""
        model = ArtistModel.from_domain(artist)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get(self, artist_id: UUID) -> Optional[Artist]:
        """Get artist by ID."""
        result = await self.session.execute(
            select(ArtistModel).where(ArtistModel.id == artist_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "name",
        artist_type: Optional[str] = None,
        country: Optional[str] = None
    ) -> Tuple[List[Artist], int]:
        """Get all artists with pagination."""
        # Build base query
        query = select(ArtistModel)
        query = self._apply_filters(query, artist_type, country)

        # Apply sorting
        if sort_by == "name":
            query = query.order_by(ArtistModel.name)
        elif sort_by == "sort_name":
            query = query.order_by(ArtistModel.sort_name)
        elif sort_by == "created_at":
            query = query.order_by(ArtistModel.created_at.desc())
        else:
            query = query.order_by(ArtistModel.name)

        # Get total count
        count_query = select(func.count()).select_from(ArtistModel)
        count_query = self._apply_filters(count_query, artist_type, country)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        models = result.scalars().all()

        artists = [m.to_domain() for m in models]
        await self._apply_album_counts(artists)
        return artists, total

    async def search(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        artist_type: Optional[str] = None,
        country: Optional[str] = None
    ) -> Tuple[List[Artist], int]:
        """Search artists by name (fuzzy search using trigram similarity)."""
        # Use PostgreSQL trigram similarity for fuzzy search
        search_query = select(ArtistModel).where(
            ArtistModel.name.ilike(f"%{query}%")
        )
        search_query = self._apply_filters(search_query, artist_type, country)
        search_query = search_query.order_by(ArtistModel.name)

        # Get total count
        count_query = select(func.count()).select_from(ArtistModel).where(
            ArtistModel.name.ilike(f"%{query}%")
        )
        count_query = self._apply_filters(count_query, artist_type, country)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply pagination
        search_query = search_query.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(search_query)
        models = result.scalars().all()

        artists = [m.to_domain() for m in models]
        await self._apply_album_counts(artists)
        return artists, total

    async def get_by_name(self, name: str) -> Optional[Artist]:
        """Get artist by exact name match."""
        result = await self.session.execute(
            select(ArtistModel).where(ArtistModel.name == name)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_discogs_id(self, discogs_id: int) -> Optional[Artist]:
        """Get artist by Discogs ID."""
        result = await self.session.execute(
            select(ArtistModel).where(ArtistModel.discogs_id == discogs_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def update(self, artist: Artist) -> Artist:
        """Update an existing artist."""
        # Get existing model
        result = await self.session.execute(
            select(ArtistModel).where(ArtistModel.id == artist.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Artist {artist.id} not found")

        # Update fields
        model.name = artist.name
        model.sort_name = artist.sort_name
        model.type = artist.type
        model.country = artist.country
        model.active_years = artist.active_years or _build_active_years(
            artist.begin_date, artist.end_date
        )
        model.disambiguation = artist.disambiguation
        model.bio = artist.bio
        model.aliases = artist.aliases
        model.notes = artist.notes
        model.image_url = artist.image_url
        model.data_source = artist.data_source
        model.verification_status = artist.verification_status

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, artist_id: UUID) -> None:
        """Delete an artist."""
        result = await self.session.execute(
            select(ArtistModel).where(ArtistModel.id == artist_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def exists(self, artist_id: UUID) -> bool:
        """Check if artist exists."""
        result = await self.session.execute(
            select(func.count()).select_from(ArtistModel).where(ArtistModel.id == artist_id)
        )
        count = result.scalar_one()
        return count > 0
