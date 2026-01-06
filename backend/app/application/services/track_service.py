"""
Track application service.

Orchestrates track-related business operations.
Security-agnostic - no authentication or authorization logic.
"""

from uuid import UUID
from typing import Optional, List, Dict, Any

from app.domain.entities import Track
from app.application.ports.unit_of_work import UnitOfWork


class TrackService:
    """Service for track business operations."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_track(
        self,
        album_id: UUID,
        side: str,
        position: str,
        title: str,
        duration: Optional[int] = None,
        **kwargs
    ) -> Track:
        """
        Create a new track.

        Business rules enforced:
        - album_id, side, position, and title are required
        - Validates album exists
        - Unique constraint on (album_id, side, position)
        """
        # Validate album exists
        async with self.uow:
            album_exists = await self.uow.album_repository.exists(album_id)
            if not album_exists:
                raise ValueError(f"Album {album_id} does not exist")

        # Create domain entity
        track = Track(
            album_id=album_id,
            side=side,
            position=position,
            title=title,
            duration=duration,
            **kwargs
        )

        # Persist within transaction
        async with self.uow:
            result = await self.uow.track_repository.add(track)
            await self.uow.commit()

        return result

    async def get_track(self, track_id: UUID) -> Optional[Track]:
        """Get a track by ID."""
        async with self.uow:
            return await self.uow.track_repository.get(track_id)

    async def get_album_tracks(self, album_id: UUID) -> List[Track]:
        """Get all tracks for an album, sorted by side and position."""
        async with self.uow:
            return await self.uow.track_repository.get_by_album(album_id)

    async def update_track(
        self,
        track_id: UUID,
        **updates
    ) -> Optional[Track]:
        """Update a track."""
        async with self.uow:
            track = await self.uow.track_repository.get(track_id)
            if not track:
                return None

            # Apply updates to domain entity
            for key, value in updates.items():
                if hasattr(track, key) and key not in ['id', 'created_at']:
                    setattr(track, key, value)

            result = await self.uow.track_repository.update(track)
            await self.uow.commit()

        return result

    async def reorder_tracks(
        self,
        album_id: UUID,
        track_positions: List[Dict[str, Any]]
    ) -> None:
        """
        Bulk reorder tracks for an album.

        Args:
            album_id: Album ID
            track_positions: List of {"track_id": UUID, "side": str, "position": str}
        """
        async with self.uow:
            await self.uow.track_repository.reorder(album_id, track_positions)
            await self.uow.commit()

    async def delete_track(self, track_id: UUID) -> bool:
        """Delete a track."""
        async with self.uow:
            track = await self.uow.track_repository.get(track_id)
            if not track:
                return False

            await self.uow.track_repository.delete(track_id)
            await self.uow.commit()

        return True
