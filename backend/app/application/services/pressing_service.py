"""
Pressing application service.

Orchestrates pressing-related business operations including matrix and packaging.
Security-agnostic - no authentication or authorization logic.
"""

from uuid import UUID
from typing import Optional, List, Tuple, Dict, Any

from app.domain.entities import Pressing, Matrix, Packaging
from app.domain.events import ActivityEvent, PressingMasterImportRequested
from app.domain.value_objects import VinylFormat, VinylSpeed, VinylSize, EditionType, SleeveType
from app.application.ports.unit_of_work import UnitOfWork
from app.config import get_settings


class PressingService:
    """Service for pressing business operations."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.activity_topic = get_settings().activity_topic

    async def create_pressing(
        self,
        album_id: UUID,
        format: VinylFormat,
        speed_rpm: VinylSpeed,
        size_inches: VinylSize,
        disc_count: int = 1,
        import_master_releases: bool = False,
        created_by: Optional[UUID] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        **kwargs
    ) -> Pressing:
        """
        Create a new pressing.

        Business rules enforced:
        - album_id, format, speed, size are required
        - disc_count must be >= 1
        - Validates album exists
        """
        # Validate album exists
        async with self.uow:
            album_exists = await self.uow.album_repository.exists(album_id)
            if not album_exists:
                raise ValueError(f"Album {album_id} does not exist")
            edition_type = kwargs.get('edition_type')
            if edition_type:
                edition_type_entry = await self.uow.lookup_repository.get_edition_type(edition_type)
                if not edition_type_entry:
                    raise ValueError(f"Edition type '{edition_type}' is not configured")

            discogs_master_id = kwargs.get('discogs_master_id')
            if import_master_releases and not discogs_master_id:
                raise ValueError("Discogs master ID is required to import releases")

        # Create domain entity
        pressing = Pressing(
            album_id=album_id,
            format=format,
            speed_rpm=speed_rpm,
            size_inches=size_inches,
            disc_count=disc_count,
            created_by=created_by,
            **kwargs
        )

        # Persist within transaction
        async with self.uow:
            result = await self.uow.pressing_repository.add(pressing)

            album = await self.uow.album_repository.get(album_id)
            summary = album.title if album else str(result.id)
            activity_event = ActivityEvent(
                operation="created",
                entity_type="pressing",
                entity_id=result.id,
                summary=summary,
                user_id=created_by,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=activity_event,
                aggregate_id=result.id,
                aggregate_type='Pressing',
                destination=self.activity_topic
            )
            if import_master_releases and result.discogs_master_id:
                master_import_event = PressingMasterImportRequested(
                    pressing_id=result.id,
                    discogs_master_id=result.discogs_master_id,
                    created_by=created_by
                )
                await self.uow.outbox_repository.add_event(
                    event=master_import_event,
                    aggregate_id=result.id,
                    aggregate_type='Pressing',
                    destination='/topic/pressing.master.import'
                )
            await self.uow.commit()

        return result

    async def get_pressing(self, pressing_id: UUID) -> Optional[Pressing]:
        """Get a pressing by ID."""
        async with self.uow:
            return await self.uow.pressing_repository.get(pressing_id)

    async def get_pressings_by_album(
        self,
        album_id: UUID,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[UUID] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get all pressings for an album with collection status."""
        async with self.uow:
            return await self.uow.pressing_repository.get_by_album(album_id, limit, offset, user_id)

    async def search_pressings(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Pressing], int]:
        """
        Search pressings with filters.

        Filters:
            - format: VinylFormat
            - speed: VinylSpeed
            - size: VinylSize
            - country: str
            - year_min: int
            - year_max: int
        """
        async with self.uow:
            return await self.uow.pressing_repository.get_all(limit, offset, filters)

    async def update_pressing(
        self,
        pressing_id: UUID,
        user_id: Optional[UUID] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        **updates
    ) -> Optional[Pressing]:
        """Update a pressing."""
        async with self.uow:
            pressing = await self.uow.pressing_repository.get(pressing_id)
            if not pressing:
                return None

            if 'edition_type' in updates and updates['edition_type']:
                edition_type_entry = await self.uow.lookup_repository.get_edition_type(updates['edition_type'])
                if not edition_type_entry:
                    raise ValueError(f"Edition type '{updates['edition_type']}' is not configured")

            # Apply updates to domain entity
            for key, value in updates.items():
                if hasattr(pressing, key) and key not in ['id', 'created_at', 'created_by']:
                    setattr(pressing, key, value)

            result = await self.uow.pressing_repository.update(pressing)

            album = await self.uow.album_repository.get(result.album_id)
            summary = album.title if album else str(result.id)
            activity_event = ActivityEvent(
                operation="updated",
                entity_type="pressing",
                entity_id=result.id,
                summary=summary,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=activity_event,
                aggregate_id=result.id,
                aggregate_type='Pressing',
                destination=self.activity_topic
            )
            await self.uow.commit()

        return result

    async def delete_pressing(
        self,
        pressing_id: UUID,
        user_id: Optional[UUID] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> bool:
        """
        Delete a pressing.

        Note: Will fail if pressing is in any collections (enforced by database).
        """
        async with self.uow:
            pressing = await self.uow.pressing_repository.get(pressing_id)
            if not pressing:
                return False

            album = await self.uow.album_repository.get(pressing.album_id)
            summary = album.title if album else str(pressing.id)
            await self.uow.pressing_repository.delete(pressing_id)

            activity_event = ActivityEvent(
                operation="deleted",
                entity_type="pressing",
                entity_id=pressing_id,
                summary=summary,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=activity_event,
                aggregate_id=pressing_id,
                aggregate_type='Pressing',
                destination=self.activity_topic
            )
            await self.uow.commit()

        return True

    async def is_pressing_in_collections(self, pressing_id: UUID) -> bool:
        """Check if pressing is in any user collections."""
        async with self.uow:
            return await self.uow.pressing_repository.is_in_collections(pressing_id)

    # ========================================================================
    # MATRIX MANAGEMENT
    # ========================================================================

    async def get_pressing_matrices(self, pressing_id: UUID) -> List[Matrix]:
        """Get all matrix codes for a pressing."""
        async with self.uow:
            return await self.uow.matrix_repository.get_by_pressing(pressing_id)

    async def add_matrix_code(
        self,
        pressing_id: UUID,
        side: str,
        matrix_code: Optional[str] = None,
        etchings: Optional[str] = None,
        stamper_info: Optional[str] = None
    ) -> Matrix:
        """Add a matrix code to a pressing."""
        # Validate pressing exists
        async with self.uow:
            pressing_exists = await self.uow.pressing_repository.exists(pressing_id)
            if not pressing_exists:
                raise ValueError(f"Pressing {pressing_id} does not exist")

        matrix = Matrix(
            pressing_id=pressing_id,
            side=side,
            matrix_code=matrix_code,
            etchings=etchings,
            stamper_info=stamper_info
        )

        async with self.uow:
            result = await self.uow.matrix_repository.add(matrix)
            await self.uow.commit()

        return result

    async def bulk_update_matrices(
        self,
        pressing_id: UUID,
        matrices_data: List[Dict[str, Any]]
    ) -> List[Matrix]:
        """
        Bulk update matrix codes for a pressing.

        Replaces all existing matrices with new ones.
        """
        # Create domain entities
        matrices = [
            Matrix(pressing_id=pressing_id, **data)
            for data in matrices_data
        ]

        async with self.uow:
            result = await self.uow.matrix_repository.bulk_upsert(pressing_id, matrices)
            await self.uow.commit()

        return result

    # ========================================================================
    # PACKAGING MANAGEMENT
    # ========================================================================

    async def get_pressing_packaging(self, pressing_id: UUID) -> Optional[Packaging]:
        """Get packaging details for a pressing."""
        async with self.uow:
            return await self.uow.packaging_repository.get_by_pressing(pressing_id)

    async def add_or_update_packaging(
        self,
        pressing_id: UUID,
        sleeve_type: SleeveType,
        **kwargs
    ) -> Packaging:
        """
        Add or update packaging details for a pressing.

        Uses upsert logic (insert if new, update if exists).
        """
        # Validate pressing exists
        async with self.uow:
            pressing_exists = await self.uow.pressing_repository.exists(pressing_id)
            if not pressing_exists:
                raise ValueError(f"Pressing {pressing_id} does not exist")

        packaging = Packaging(
            pressing_id=pressing_id,
            sleeve_type=sleeve_type,
            **kwargs
        )

        async with self.uow:
            result = await self.uow.packaging_repository.upsert(packaging)
            await self.uow.commit()

        return result

    async def get_pressings_with_details(
        self,
        query: Optional[str] = None,
        artist_id: Optional[UUID] = None,
        album_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[UUID] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get pressings with enriched artist and album details.

        Returns pressings with joined artist/album data for hierarchical display.
        """
        async with self.uow:
            return await self.uow.pressing_repository.get_all_with_details(
                query, artist_id, album_id, limit, offset, user_id
            )
