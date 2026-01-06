"""
Artist application service.

Orchestrates artist-related business operations.
Security-agnostic - no authentication or authorization logic.
"""

from uuid import UUID
from typing import Optional, List, Tuple

from app.domain.entities import Artist
from app.domain.value_objects import ArtistType
from app.domain.events import ArtistCreated, ArtistUpdated, ArtistDeleted, ActivityEvent
from app.application.ports.unit_of_work import UnitOfWork
from app.config import get_settings


class ArtistService:
    """Service for artist business operations."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.activity_topic = get_settings().activity_topic

    async def create_artist(
        self,
        name: str,
        type: ArtistType = ArtistType.PERSON,
        country: Optional[str] = None,
        created_by: Optional[UUID] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        **kwargs
    ) -> Artist:
        """
        Create a new artist.

        Business rules enforced:
        - Name is required (enforced by domain entity)
        - Sort name auto-generated if not provided
        """
        # Create domain entity (business rules enforced)
        async with self.uow:
            artist_type = await self.uow.lookup_repository.get_artist_type(type)
            if not artist_type:
                raise ValueError(f"Artist type '{type}' is not configured")

        artist = Artist(
            name=name,
            type=type,
            country=country,
            created_by=created_by,
            **kwargs
        )

        # Persist within transaction
        async with self.uow:
            result = await self.uow.artist_repository.add(artist)

            # Emit domain event
            event = ArtistCreated(
                artist_id=result.id,
                name=result.name,
                artist_type=result.type,
                created_by=created_by
            )
            await self.uow.outbox_repository.add_event(
                event=event,
                aggregate_id=result.id,
                aggregate_type='Artist',
                destination='/topic/artist.created'
            )

            activity_event = ActivityEvent(
                operation="created",
                entity_type="artist",
                entity_id=result.id,
                summary=result.name,
                user_id=created_by,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=activity_event,
                aggregate_id=result.id,
                aggregate_type='Artist',
                destination=self.activity_topic
            )

            await self.uow.commit()

        return result

    async def get_artist(self, artist_id: UUID) -> Optional[Artist]:
        """Get an artist by ID."""
        async with self.uow:
            return await self.uow.artist_repository.get(artist_id)

    async def search_artists(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        artist_type: Optional[str] = None,
        country: Optional[str] = None
    ) -> Tuple[List[Artist], int]:
        """Search artists by name (fuzzy search)."""
        async with self.uow:
            return await self.uow.artist_repository.search(
                query,
                limit,
                offset,
                artist_type=artist_type,
                country=country
            )

    async def list_artists(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "name",
        artist_type: Optional[str] = None,
        country: Optional[str] = None
    ) -> Tuple[List[Artist], int]:
        """List all artists with pagination."""
        async with self.uow:
            return await self.uow.artist_repository.get_all(
                limit,
                offset,
                sort_by,
                artist_type=artist_type,
                country=country
            )

    async def update_artist(
        self,
        artist_id: UUID,
        user_id: Optional[UUID] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        **updates
    ) -> Optional[Artist]:
        """
        Update an artist.

        Only provided fields are updated.
        """
        async with self.uow:
            artist = await self.uow.artist_repository.get(artist_id)
            if not artist:
                return None

            if 'artist_type' in updates and 'type' not in updates:
                updates['type'] = updates.pop('artist_type')

            if 'type' in updates:
                artist_type = await self.uow.lookup_repository.get_artist_type(updates['type'])
                if not artist_type:
                    raise ValueError(f"Artist type '{updates['type']}' is not configured")

            # Apply updates using domain entity method
            artist.update(**updates)

            result = await self.uow.artist_repository.update(artist)

            # Emit domain event
            event = ArtistUpdated(
                artist_id=result.id,
                updated_fields=updates
            )
            await self.uow.outbox_repository.add_event(
                event=event,
                aggregate_id=result.id,
                aggregate_type='Artist',
                destination='/topic/artist.updated'
            )

            activity_event = ActivityEvent(
                operation="updated",
                entity_type="artist",
                entity_id=result.id,
                summary=result.name,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=activity_event,
                aggregate_id=result.id,
                aggregate_type='Artist',
                destination=self.activity_topic
            )

            await self.uow.commit()

        return result

    async def delete_artist(
        self,
        artist_id: UUID,
        user_id: Optional[UUID] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> bool:
        """
        Delete an artist.

        Note: Will fail if artist has albums (enforced by database constraint).
        """
        async with self.uow:
            artist = await self.uow.artist_repository.get(artist_id)
            if not artist:
                return False

            await self.uow.artist_repository.delete(artist_id)

            # Emit domain event
            event = ArtistDeleted(artist_id=artist_id)
            await self.uow.outbox_repository.add_event(
                event=event,
                aggregate_id=artist_id,
                aggregate_type='Artist',
                destination='/topic/artist.deleted'
            )

            activity_event = ActivityEvent(
                operation="deleted",
                entity_type="artist",
                entity_id=artist_id,
                summary=artist.name,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=activity_event,
                aggregate_id=artist_id,
                aggregate_type='Artist',
                destination=self.activity_topic
            )

            await self.uow.commit()

        return True

    async def check_artist_exists(self, artist_id: UUID) -> bool:
        """Check if an artist exists."""
        async with self.uow:
            return await self.uow.artist_repository.exists(artist_id)
