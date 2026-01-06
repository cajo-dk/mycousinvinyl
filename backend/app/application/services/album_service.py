"""
Album application service.

Orchestrates album-related business operations including genre/style management.
Security-agnostic - no authentication or authorization logic.
"""

from uuid import UUID
from typing import Optional, List, Tuple, Dict, Any
from datetime import date

from app.domain.entities import Album
from app.domain.events import ActivityEvent
from app.domain.value_objects import ReleaseType
from app.application.ports.unit_of_work import UnitOfWork
from app.config import get_settings


class AlbumService:
    """Service for album business operations."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.activity_topic = get_settings().activity_topic

    async def create_album(
        self,
        title: str,
        primary_artist_id: UUID,
        release_type: ReleaseType = ReleaseType.STUDIO,
        genre_ids: Optional[List[UUID]] = None,
        style_ids: Optional[List[UUID]] = None,
        created_by: Optional[UUID] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        **kwargs
    ) -> Album:
        """
        Create a new album.

        Business rules enforced:
        - Title and primary_artist_id are required (enforced by domain entity)
        - Cannot reference self as original release
        - Validates artist exists
        """
        # Validate artist and release type exist
        async with self.uow:
            artist_exists = await self.uow.artist_repository.exists(primary_artist_id)
            if not artist_exists:
                raise ValueError(f"Artist {primary_artist_id} does not exist")
            release_type_entry = await self.uow.lookup_repository.get_release_type(release_type)
            if not release_type_entry:
                raise ValueError(f"Release type '{release_type}' is not configured")

        # Create domain entity
        album = Album(
            title=title,
            primary_artist_id=primary_artist_id,
            release_type=release_type,
            genre_ids=genre_ids or [],
            style_ids=style_ids or [],
            created_by=created_by,
            **kwargs
        )

        # Persist within transaction
        async with self.uow:
            result = await self.uow.album_repository.add(album)

            activity_event = ActivityEvent(
                operation="created",
                entity_type="album",
                entity_id=result.id,
                summary=result.title,
                user_id=created_by,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=activity_event,
                aggregate_id=result.id,
                aggregate_type='Album',
                destination=self.activity_topic
            )
            await self.uow.commit()

        return result

    async def get_album(self, album_id: UUID) -> Optional[Album]:
        """Get an album by ID with genres and styles."""
        async with self.uow:
            return await self.uow.album_repository.get(album_id)

    async def search_albums(
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
            - genres: List[UUID]
            - styles: List[UUID]
            - year_min: int
            - year_max: int
            - artist_id: UUID
            - release_type: str
            - country: str
        """
        async with self.uow:
            return await self.uow.album_repository.search(
                query, filters, sort_by, limit, offset
            )

    async def list_albums(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "title"
    ) -> Tuple[List[Album], int]:
        """List all albums with pagination."""
        async with self.uow:
            return await self.uow.album_repository.get_all(limit, offset, sort_by)

    async def get_albums_by_artist(
        self,
        artist_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Album], int]:
        """Get all albums by an artist."""
        async with self.uow:
            return await self.uow.album_repository.get_by_artist(artist_id, limit, offset)

    async def update_album(
        self,
        album_id: UUID,
        user_id: Optional[UUID] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        **updates
    ) -> Optional[Album]:
        """
        Update an album.

        Validates primary_artist_id if being updated.
        """
        async with self.uow:
            album = await self.uow.album_repository.get(album_id)
            if not album:
                return None

            # Validate artist if being updated
            if 'primary_artist_id' in updates:
                artist_exists = await self.uow.artist_repository.exists(updates['primary_artist_id'])
                if not artist_exists:
                    raise ValueError(f"Artist {updates['primary_artist_id']} does not exist")

            if 'release_type' in updates:
                release_type_entry = await self.uow.lookup_repository.get_release_type(updates['release_type'])
                if not release_type_entry:
                    raise ValueError(f"Release type '{updates['release_type']}' is not configured")

            # Apply updates using domain entity method
            album.update(**updates)

            result = await self.uow.album_repository.update(album)

            activity_event = ActivityEvent(
                operation="updated",
                entity_type="album",
                entity_id=result.id,
                summary=result.title,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=activity_event,
                aggregate_id=result.id,
                aggregate_type='Album',
                destination=self.activity_topic
            )
            await self.uow.commit()

        return result

    async def delete_album(
        self,
        album_id: UUID,
        user_id: Optional[UUID] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> bool:
        """
        Delete an album.

        Note: Will fail if album has pressings (enforced by database constraint).
        """
        async with self.uow:
            album = await self.uow.album_repository.get(album_id)
            if not album:
                return False

            await self.uow.album_repository.delete(album_id)

            activity_event = ActivityEvent(
                operation="deleted",
                entity_type="album",
                entity_id=album_id,
                summary=album.title,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=activity_event,
                aggregate_id=album_id,
                aggregate_type='Album',
                destination=self.activity_topic
            )
            await self.uow.commit()

        return True

    async def check_album_exists(self, album_id: UUID) -> bool:
        """Check if an album exists."""
        async with self.uow:
            return await self.uow.album_repository.exists(album_id)

    async def album_has_pressings(self, album_id: UUID) -> bool:
        """Check if an album has any pressings (useful before deletion)."""
        async with self.uow:
            return await self.uow.album_repository.has_pressings(album_id)

    async def get_albums_with_details(
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
        Get albums with enriched artist details and pressing counts.

        Returns albums grouped with artist information and pressing counts
        for hierarchical display in UI.
        """
        async with self.uow:
            return await self.uow.album_repository.get_all_with_details(
                query=query,
                artist_id=artist_id,
                genre_ids=genre_ids,
                style_ids=style_ids,
                release_type=release_type,
                year_min=year_min,
                year_max=year_max,
                limit=limit,
                offset=offset,
                user_id=user_id
            )
