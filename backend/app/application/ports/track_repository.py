"""Track repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.domain.entities import Track


class TrackRepository(ABC):
    """Repository interface for Track entities."""

    @abstractmethod
    async def add(self, track: Track) -> Track:
        """Add a new track."""
        pass

    @abstractmethod
    async def get(self, track_id: UUID) -> Optional[Track]:
        """Get track by ID."""
        pass

    @abstractmethod
    async def get_by_album(self, album_id: UUID) -> List[Track]:
        """Get all tracks for an album, sorted by side and position."""
        pass

    @abstractmethod
    async def update(self, track: Track) -> Track:
        """Update an existing track."""
        pass

    @abstractmethod
    async def delete(self, track_id: UUID) -> None:
        """Delete a track."""
        pass

    @abstractmethod
    async def reorder(self, album_id: UUID, track_positions: List[Dict[str, Any]]) -> None:
        """
        Bulk reorder tracks for an album.

        Args:
            album_id: Album ID
            track_positions: List of {"track_id": UUID, "side": str, "position": str}
        """
        pass

    @abstractmethod
    async def exists(self, track_id: UUID) -> bool:
        """Check if track exists."""
        pass
