"""Track repository PostgreSQL adapter."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.track_repository import TrackRepository
from app.domain.entities import Track
from app.adapters.postgres.models import TrackModel


class TrackRepositoryAdapter(TrackRepository):
    """PostgreSQL implementation of TrackRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, track: Track) -> Track:
        """Add a new track."""
        model = TrackModel.from_domain(track)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get(self, track_id: UUID) -> Optional[Track]:
        """Get track by ID."""
        result = await self.session.execute(
            select(TrackModel).where(TrackModel.id == track_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_album(self, album_id: UUID) -> List[Track]:
        """Get all tracks for an album, sorted by side and position."""
        result = await self.session.execute(
            select(TrackModel)
            .where(TrackModel.album_id == album_id)
            .order_by(TrackModel.side, TrackModel.position)
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def update(self, track: Track) -> Track:
        """Update an existing track."""
        result = await self.session.execute(
            select(TrackModel).where(TrackModel.id == track.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Track {track.id} not found")

        # Update fields
        model.album_id = track.album_id
        model.side = track.side
        model.position = track.position
        model.title = track.title
        model.duration = track.duration
        model.songwriters = track.songwriters
        model.notes = track.notes

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, track_id: UUID) -> None:
        """Delete a track."""
        result = await self.session.execute(
            select(TrackModel).where(TrackModel.id == track_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def reorder(self, album_id: UUID, track_positions: List[Dict[str, Any]]) -> None:
        """
        Bulk reorder tracks for an album.

        Args:
            album_id: Album ID
            track_positions: List of {"track_id": UUID, "side": str, "position": str}
        """
        for position_data in track_positions:
            track_id = position_data['track_id']
            result = await self.session.execute(
                select(TrackModel).where(TrackModel.id == track_id)
            )
            model = result.scalar_one_or_none()

            if model:
                model.side = position_data['side']
                model.position = position_data['position']

        await self.session.flush()

    async def exists(self, track_id: UUID) -> bool:
        """Check if track exists."""
        result = await self.session.execute(
            select(func.count()).select_from(TrackModel).where(TrackModel.id == track_id)
        )
        count = result.scalar_one()
        return count > 0
