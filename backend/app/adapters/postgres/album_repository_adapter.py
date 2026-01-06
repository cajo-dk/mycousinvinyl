"""Album repository PostgreSQL adapter."""

from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, or_, and_, exists, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.ports.album_repository import AlbumRepository
from app.domain.entities import Album
from app.adapters.postgres.models import AlbumModel, GenreModel, StyleModel, album_genres, album_styles


class AlbumRepositoryAdapter(AlbumRepository):
    """PostgreSQL implementation of AlbumRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, album: Album) -> Album:
        """Add a new album."""
        model = AlbumModel.from_domain(album)
        self.session.add(model)
        await self.session.flush()

        # Add genre and style associations
        if album.genre_ids:
            for genre_id in album.genre_ids:
                await self.session.execute(
                    album_genres.insert().values(album_id=model.id, genre_id=genre_id)
                )

        if album.style_ids:
            for style_id in album.style_ids:
                await self.session.execute(
                    album_styles.insert().values(album_id=model.id, style_id=style_id)
                )

        await self.session.flush()
        await self.session.refresh(model, ['genres', 'styles'])
        return model.to_domain()

    async def get(self, album_id: UUID) -> Optional[Album]:
        """Get album by ID with genres and styles."""
        result = await self.session.execute(
            select(AlbumModel)
            .where(AlbumModel.id == album_id)
            .options(selectinload(AlbumModel.genres), selectinload(AlbumModel.styles))
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "title"
    ) -> Tuple[List[Album], int]:
        """Get all albums with pagination."""
        # Build base query
        query = select(AlbumModel).options(
            selectinload(AlbumModel.genres),
            selectinload(AlbumModel.styles)
        )

        # Apply sorting
        if sort_by == "title":
            query = query.order_by(AlbumModel.title)
        elif sort_by == "year":
            query = query.order_by(AlbumModel.original_release_year.desc())
        elif sort_by == "created_at":
            query = query.order_by(AlbumModel.created_at.desc())
        else:
            query = query.order_by(AlbumModel.title)

        # Get total count
        count_query = select(func.count()).select_from(AlbumModel)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        models = result.scalars().all()

        return [m.to_domain() for m in models], total

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
            - genres: List[UUID] - Filter by genre IDs (OR)
            - styles: List[UUID] - Filter by style IDs (OR)
            - year_min: int - Minimum release year
            - year_max: int - Maximum release year
            - artist_id: UUID - Filter by primary artist
            - release_type: str - Filter by release type
            - country: str - Filter by country of origin
        """
        filters = filters or {}

        # Build base query
        search_query = select(AlbumModel).options(
            selectinload(AlbumModel.genres),
            selectinload(AlbumModel.styles)
        )

        # Build where clauses
        where_clauses = []

        # Full-text search
        if query:
            # Use tsvector for full-text search
            search_query = search_query.where(
                AlbumModel.search_vector.op('@@')(func.plainto_tsquery('english', query))
            )

        # Genre filter (OR within genres)
        if 'genres' in filters and filters['genres']:
            search_query = search_query.join(
                album_genres, AlbumModel.id == album_genres.c.album_id
            ).where(album_genres.c.genre_id.in_(filters['genres']))

        # Style filter (OR within styles)
        if 'styles' in filters and filters['styles']:
            search_query = search_query.join(
                album_styles, AlbumModel.id == album_styles.c.album_id
            ).where(album_styles.c.style_id.in_(filters['styles']))

        # Year range filter
        if 'year_min' in filters:
            where_clauses.append(AlbumModel.original_release_year >= filters['year_min'])
        if 'year_max' in filters:
            where_clauses.append(AlbumModel.original_release_year <= filters['year_max'])

        # Artist filter
        if 'artist_id' in filters:
            where_clauses.append(AlbumModel.primary_artist_id == filters['artist_id'])

        # Release type filter
        if 'release_type' in filters:
            where_clauses.append(AlbumModel.release_type == filters['release_type'])

        # Country filter
        if 'country' in filters:
            where_clauses.append(AlbumModel.country_of_origin == filters['country'])

        # Apply where clauses
        if where_clauses:
            search_query = search_query.where(and_(*where_clauses))

        # Get total count (before pagination)
        count_query = select(func.count()).select_from(search_query.alias())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply sorting
        if sort_by == "relevance" and query:
            # Sort by relevance (ts_rank)
            search_query = search_query.order_by(
                func.ts_rank(
                    AlbumModel.search_vector,
                    func.plainto_tsquery('english', query)
                ).desc()
            )
        elif sort_by == "title":
            search_query = search_query.order_by(AlbumModel.title)
        elif sort_by == "year_desc":
            search_query = search_query.order_by(AlbumModel.original_release_year.desc())
        elif sort_by == "year_asc":
            search_query = search_query.order_by(AlbumModel.original_release_year.asc())
        else:
            search_query = search_query.order_by(AlbumModel.title)

        # Apply pagination
        search_query = search_query.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(search_query)
        models = result.scalars().all()

        return [m.to_domain() for m in models], total

    async def get_by_artist(
        self,
        artist_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Album], int]:
        """Get all albums by an artist."""
        query = select(AlbumModel).where(
            AlbumModel.primary_artist_id == artist_id
        ).options(
            selectinload(AlbumModel.genres),
            selectinload(AlbumModel.styles)
        ).order_by(AlbumModel.original_release_year.desc())

        # Get total count
        count_query = select(func.count()).select_from(AlbumModel).where(
            AlbumModel.primary_artist_id == artist_id
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        models = result.scalars().all()

        return [m.to_domain() for m in models], total

    async def get_by_discogs_id(self, discogs_id: int) -> Optional[Album]:
        """Get album by Discogs ID."""
        result = await self.session.execute(
            select(AlbumModel)
            .where(AlbumModel.discogs_id == discogs_id)
            .options(selectinload(AlbumModel.genres), selectinload(AlbumModel.styles))
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_title_and_artist(self, artist_id: UUID, title: str) -> Optional[Album]:
        """Get album by title for a given artist (case-insensitive)."""
        normalized = title.strip().lower()
        result = await self.session.execute(
            select(AlbumModel)
            .where(
                AlbumModel.primary_artist_id == artist_id,
                func.lower(AlbumModel.title) == normalized
            )
            .options(selectinload(AlbumModel.genres), selectinload(AlbumModel.styles))
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def search_by_title_and_artist(
        self,
        artist_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Album]:
        """Search albums by title for a given artist (partial match)."""
        result = await self.session.execute(
            select(AlbumModel)
            .where(
                AlbumModel.primary_artist_id == artist_id,
                AlbumModel.title.ilike(f"%{query}%")
            )
            .options(selectinload(AlbumModel.genres), selectinload(AlbumModel.styles))
            .order_by(AlbumModel.title)
            .limit(limit)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def update(self, album: Album) -> Album:
        """Update an existing album."""
        # Get existing model
        result = await self.session.execute(
            select(AlbumModel).where(AlbumModel.id == album.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Album {album.id} not found")

        # Update fields
        model.title = album.title
        model.primary_artist_id = album.primary_artist_id
        model.release_type = album.release_type
        model.original_release_year = album.original_release_year
        model.original_release_date = album.original_release_date
        model.country_of_origin = album.country_of_origin
        model.label = album.label
        model.catalog_number_base = album.catalog_number_base
        model.description = album.description
        model.image_url = album.image_url
        model.original_release_id = album.original_release_id
        model.data_source = album.data_source
        model.verification_status = album.verification_status

        # Update genre associations
        await self.session.execute(
            album_genres.delete().where(album_genres.c.album_id == album.id)
        )
        if album.genre_ids:
            for genre_id in album.genre_ids:
                await self.session.execute(
                    album_genres.insert().values(album_id=album.id, genre_id=genre_id)
                )

        # Update style associations
        await self.session.execute(
            album_styles.delete().where(album_styles.c.album_id == album.id)
        )
        if album.style_ids:
            for style_id in album.style_ids:
                await self.session.execute(
                    album_styles.insert().values(album_id=album.id, style_id=style_id)
                )

        await self.session.flush()
        await self.session.refresh(model, ['genres', 'styles'])
        return model.to_domain()

    async def delete(self, album_id: UUID) -> None:
        """Delete an album."""
        result = await self.session.execute(
            select(AlbumModel).where(AlbumModel.id == album_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def exists(self, album_id: UUID) -> bool:
        """Check if album exists."""
        result = await self.session.execute(
            select(func.count()).select_from(AlbumModel).where(AlbumModel.id == album_id)
        )
        count = result.scalar_one()
        return count > 0

    async def has_pressings(self, album_id: UUID) -> bool:
        """Check if album has any pressings."""
        from app.adapters.postgres.models import PressingModel

        result = await self.session.execute(
            select(func.count()).select_from(PressingModel).where(
                PressingModel.album_id == album_id
            )
        )
        count = result.scalar_one()
        return count > 0

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
        offset: int = 0,
        user_id: Optional[UUID] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get albums with joined artist details and pressing counts.

        Returns enriched data for hierarchical display in UI.
        """
        from app.adapters.postgres.models import ArtistModel, PressingModel, CollectionItemModel
        from sqlalchemy.orm import selectinload

        # Build subquery to check if user has any collection items for this album
        if user_id:
            in_collection_subquery = (
                exists(
                    select(1)
                    .select_from(CollectionItemModel)
                    .join(PressingModel, CollectionItemModel.pressing_id == PressingModel.id)
                    .where(
                        PressingModel.album_id == AlbumModel.id,
                        CollectionItemModel.user_id == user_id
                    )
                )
            ).label('in_user_collection')
        else:
            in_collection_subquery = literal(False).label('in_user_collection')

        # Build base query with joins
        stmt = select(
            AlbumModel,
            ArtistModel,
            func.count(PressingModel.id).label('pressing_count'),
            in_collection_subquery
        ).join(
            ArtistModel, AlbumModel.primary_artist_id == ArtistModel.id
        ).outerjoin(
            PressingModel, PressingModel.album_id == AlbumModel.id
        ).options(
            selectinload(AlbumModel.genres),
            selectinload(AlbumModel.styles)
        ).group_by(
            AlbumModel.id,
            ArtistModel.id
        )

        # Add filters
        where_clauses = []
        if query:
            where_clauses.append(
                or_(
                    AlbumModel.title.ilike(f"%{query}%"),
                    ArtistModel.name.ilike(f"%{query}%")
                )
            )
        if artist_id:
            where_clauses.append(AlbumModel.primary_artist_id == artist_id)
        if release_type:
            where_clauses.append(AlbumModel.release_type == release_type)
        if year_min is not None:
            where_clauses.append(AlbumModel.original_release_year >= year_min)
        if year_max is not None:
            where_clauses.append(AlbumModel.original_release_year <= year_max)
        if genre_ids:
            genre_exists = (
                select(album_genres.c.album_id)
                .where(
                    album_genres.c.album_id == AlbumModel.id,
                    album_genres.c.genre_id.in_(genre_ids)
                )
                .exists()
            )
            where_clauses.append(genre_exists)
        if style_ids:
            style_exists = (
                select(album_styles.c.album_id)
                .where(
                    album_styles.c.album_id == AlbumModel.id,
                    album_styles.c.style_id.in_(style_ids)
                )
                .exists()
            )
            where_clauses.append(style_exists)

        if where_clauses:
            stmt = stmt.where(and_(*where_clauses))

        # Get total count
        count_stmt = select(func.count(AlbumModel.id)).select_from(AlbumModel).join(
            ArtistModel, AlbumModel.primary_artist_id == ArtistModel.id
        )
        if where_clauses:
            count_stmt = count_stmt.where(and_(*where_clauses))

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Apply ordering and pagination
        stmt = stmt.order_by(
            ArtistModel.sort_name.asc().nullslast(),
            ArtistModel.name.asc(),
            AlbumModel.original_release_year.asc().nullslast(),
            AlbumModel.title.asc()
        ).limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(stmt)
        rows = result.all()

        # Build enriched response data
        items = []
        for album, artist, pressing_count, in_user_collection in rows:
            # Access genres through the relationship (already eager loaded)
            genres = [g.name for g in album.genres]
            styles = [s.name for s in album.styles]

            items.append({
                "album": album,
                "artist": artist,
                "genres": genres,
                "styles": styles,
                "pressing_count": pressing_count,
                "in_user_collection": in_user_collection
            })

        return items, total
