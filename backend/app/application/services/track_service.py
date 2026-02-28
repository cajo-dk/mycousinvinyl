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
        credits = kwargs.pop("credits", None)
        layout_type = kwargs.pop("layout_type", "track")
        parent_track_id = kwargs.pop("parent_track_id", None)
        performers = kwargs.pop("performers", None) or []
        layout_order = kwargs.pop("layout_order", 0)
        track = Track(
            album_id=album_id,
            side=side,
            position=position,
            title=title,
            duration=duration,
            layout_type=layout_type,
            parent_track_id=parent_track_id,
            performers=performers,
            layout_order=layout_order,
            notes=credits,
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
                if key == "credits":
                    track.notes = value
                    continue
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

    async def replace_album_tracks(self, album_id: UUID, tracks: List[Dict[str, Any]]) -> List[Track]:
        """
        Replace all tracks for an album in a single transaction.

        Existing tracks are removed before new entries are inserted.
        """
        async with self.uow:
            album_exists = await self.uow.album_repository.exists(album_id)
            if not album_exists:
                raise ValueError(f"Album {album_id} does not exist")

            existing = await self.uow.track_repository.get_by_album(album_id)
            for track in existing:
                await self.uow.track_repository.delete(track.id)

            created: List[Track] = []
            for order, entry in enumerate(tracks):
                track = Track(
                    album_id=album_id,
                    side=entry["side"],
                    position=entry["position"],
                    title=entry["title"],
                    duration=entry.get("duration"),
                    notes=entry.get("credits"),
                    layout_type=entry.get("layout_type", "track"),
                    performers=entry.get("performers") or [],
                    layout_order=order,
                )
                created.append(await self.uow.track_repository.add(track))

            for index, entry in enumerate(tracks):
                parent_index = entry.get("parent_index")
                if parent_index is None:
                    continue
                if not isinstance(parent_index, int):
                    continue
                if parent_index < 0 or parent_index >= len(created):
                    continue
                child = created[index]
                parent = created[parent_index]
                child.parent_track_id = parent.id
                child = await self.uow.track_repository.update(child)
                created[index] = child

            await self.uow.commit()
            return created
