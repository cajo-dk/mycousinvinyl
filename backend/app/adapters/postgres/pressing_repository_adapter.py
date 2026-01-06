"""Pressing repository PostgreSQL adapter."""

from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.pressing_repository import PressingRepository
from app.domain.entities import Pressing
from app.adapters.postgres.models import PressingModel


class PressingRepositoryAdapter(PressingRepository):
    """PostgreSQL implementation of PressingRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, pressing: Pressing) -> Pressing:
        """Add a new pressing."""
        model = PressingModel.from_domain(pressing)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get(self, pressing_id: UUID) -> Optional[Pressing]:
        """Get pressing by ID."""
        result = await self.session.execute(
            select(PressingModel).where(PressingModel.id == pressing_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Pressing], int]:
        """Get all pressings with optional filters."""
        filters = filters or {}

        # Build base query
        query = select(PressingModel)

        # Build filter conditions
        where_clauses = []

        if 'format' in filters:
            where_clauses.append(PressingModel.format == filters['format'])

        if 'speed' in filters:
            where_clauses.append(PressingModel.speed_rpm == filters['speed'])

        if 'size' in filters:
            where_clauses.append(PressingModel.size_inches == filters['size'])

        if 'country' in filters:
            where_clauses.append(PressingModel.pressing_country == filters['country'])

        if 'year_min' in filters:
            where_clauses.append(PressingModel.pressing_year >= filters['year_min'])

        if 'year_max' in filters:
            where_clauses.append(PressingModel.pressing_year <= filters['year_max'])

        # Apply filters
        if where_clauses:
            query = query.where(and_(*where_clauses))

        # Get total count
        count_query = select(func.count()).select_from(query.alias())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply pagination and sorting
        query = query.order_by(PressingModel.pressing_year.desc()).limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        models = result.scalars().all()

        return [m.to_domain() for m in models], total

    async def get_by_album(
        self,
        album_id: UUID,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[UUID] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get all pressings for an album with collection status."""
        from app.adapters.postgres.models import CollectionItemModel
        from sqlalchemy import exists, literal

        # Build subquery to check if user has this pressing in their collection
        if user_id:
            in_collection_subquery = (
                exists(
                    select(1)
                    .select_from(CollectionItemModel)
                    .where(
                        CollectionItemModel.pressing_id == PressingModel.id,
                        CollectionItemModel.user_id == user_id
                    )
                )
            ).label('in_user_collection')
        else:
            in_collection_subquery = literal(False).label('in_user_collection')

        # Build query with collection status
        query = select(
            PressingModel,
            in_collection_subquery
        ).where(
            PressingModel.album_id == album_id
        ).order_by(PressingModel.pressing_year.desc())

        # Get total count
        count_query = select(func.count()).select_from(PressingModel).where(
            PressingModel.album_id == album_id
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        rows = result.all()

        # Build response with collection status
        items = []
        for pressing_model, in_user_collection in rows:
            items.append({
                "pressing": pressing_model.to_domain(),
                "in_user_collection": in_user_collection
            })

        return items, total

    async def update(self, pressing: Pressing) -> Pressing:
        """Update an existing pressing."""
        result = await self.session.execute(
            select(PressingModel).where(PressingModel.id == pressing.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Pressing {pressing.id} not found")

        # Update fields
        model.album_id = pressing.album_id
        model.format = pressing.format
        model.speed_rpm = pressing.speed_rpm
        model.size_inches = pressing.size_inches
        model.disc_count = pressing.disc_count
        model.pressing_country = pressing.pressing_country
        model.pressing_year = pressing.pressing_year
        model.pressing_plant = pressing.pressing_plant
        model.mastering_engineer = pressing.mastering_engineer
        model.mastering_studio = pressing.mastering_studio
        model.vinyl_color = pressing.vinyl_color
        model.label_design = pressing.label_design
        model.image_url = pressing.image_url
        model.edition_type = pressing.edition_type
        model.barcode = pressing.barcode
        model.notes = pressing.notes
        model.discogs_release_id = pressing.discogs_release_id
        model.discogs_master_id = pressing.discogs_master_id
        model.master_title = pressing.master_title
        model.data_source = pressing.data_source
        model.verification_status = pressing.verification_status

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, pressing_id: UUID) -> None:
        """Delete a pressing."""
        result = await self.session.execute(
            select(PressingModel).where(PressingModel.id == pressing_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def exists(self, pressing_id: UUID) -> bool:
        """Check if pressing exists."""
        result = await self.session.execute(
            select(func.count()).select_from(PressingModel).where(
                PressingModel.id == pressing_id
            )
        )
        count = result.scalar_one()
        return count > 0

    async def is_in_collections(self, pressing_id: UUID) -> bool:
        """Check if pressing is in any user collections."""
        from app.adapters.postgres.models import CollectionItemModel

        result = await self.session.execute(
            select(func.count()).select_from(CollectionItemModel).where(
                CollectionItemModel.pressing_id == pressing_id
            )
        )
        count = result.scalar_one()
        return count > 0

    async def has_children(self, pressing_id: UUID) -> bool:
        """
        Check if pressing has child pressings (is a master).

        Note: This concept is deprecated. With the master_title field,
        we no longer track master-child relationships via FK.
        """
        # Always return False as we no longer have master-child FK relationships
        return False

    async def get_master_by_discogs_id(self, discogs_master_id: int) -> Optional[Pressing]:
        """
        Get pressing by Discogs master ID.

        Note: The concept of "master pressing" with FK relationships is deprecated.
        This now simply returns any pressing with the given discogs_master_id.
        """
        result = await self.session.execute(
            select(PressingModel).where(
                PressingModel.discogs_master_id == discogs_master_id
            ).limit(1)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_discogs_release_id(self, discogs_release_id: int) -> Optional[Pressing]:
        """Get pressing by Discogs release ID."""
        result = await self.session.execute(
            select(PressingModel).where(
                PressingModel.discogs_release_id == discogs_release_id
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all_with_details(
        self,
        query: Optional[str] = None,
        artist_id: Optional[UUID] = None,
        album_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[UUID] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get pressings with joined artist and album details.

        Returns enriched data for hierarchical display in UI.
        """
        from app.adapters.postgres.models import AlbumModel, ArtistModel, PackagingModel, CollectionItemModel
        from sqlalchemy import exists, literal

        # Build subquery to check if user has this pressing in their collection
        if user_id:
            in_collection_subquery = (
                exists(
                    select(1)
                    .select_from(CollectionItemModel)
                    .where(
                        CollectionItemModel.pressing_id == PressingModel.id,
                        CollectionItemModel.user_id == user_id
                    )
                )
            ).label('in_user_collection')
        else:
            in_collection_subquery = literal(False).label('in_user_collection')

        # Build base query with joins
        stmt = select(
            PressingModel,
            AlbumModel,
            ArtistModel,
            PackagingModel,
            in_collection_subquery
        ).join(
            AlbumModel, PressingModel.album_id == AlbumModel.id
        ).join(
            ArtistModel, AlbumModel.primary_artist_id == ArtistModel.id
        ).outerjoin(
            PackagingModel, PackagingModel.pressing_id == PressingModel.id
        )

        # Add filters
        where_clauses = []
        if query:
            from sqlalchemy import or_
            where_clauses.append(
                or_(
                    AlbumModel.title.ilike(f"%{query}%"),
                    ArtistModel.name.ilike(f"%{query}%")
                )
            )
        if artist_id:
            where_clauses.append(AlbumModel.primary_artist_id == artist_id)
        if album_id:
            where_clauses.append(PressingModel.album_id == album_id)

        if where_clauses:
            stmt = stmt.where(and_(*where_clauses))

        # Get total count
        count_stmt = select(func.count(PressingModel.id)).select_from(PressingModel).join(
            AlbumModel, PressingModel.album_id == AlbumModel.id
        ).join(
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
            AlbumModel.title.asc(),
            PressingModel.pressing_year.asc().nullslast()
        ).limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(stmt)
        rows = result.all()

        # Build enriched response data
        items = []
        for pressing, album, artist, packaging, in_user_collection in rows:
            items.append({
                "pressing": pressing,
                "album": album,
                "artist": artist,
                "packaging": packaging,
                "in_user_collection": in_user_collection
            })

        return items, total
