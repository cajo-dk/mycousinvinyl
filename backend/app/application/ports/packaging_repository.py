"""Packaging repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import Packaging


class PackagingRepository(ABC):
    """Repository interface for Packaging entities."""

    @abstractmethod
    async def add(self, packaging: Packaging) -> Packaging:
        """Add packaging details for a pressing."""
        pass

    @abstractmethod
    async def get(self, packaging_id: UUID) -> Optional[Packaging]:
        """Get packaging by ID."""
        pass

    @abstractmethod
    async def get_by_pressing(self, pressing_id: UUID) -> Optional[Packaging]:
        """Get packaging for a pressing (one-to-one relationship)."""
        pass

    @abstractmethod
    async def update(self, packaging: Packaging) -> Packaging:
        """Update packaging details."""
        pass

    @abstractmethod
    async def delete(self, packaging_id: UUID) -> None:
        """Delete packaging."""
        pass

    @abstractmethod
    async def upsert(self, packaging: Packaging) -> Packaging:
        """Upsert packaging (update if exists, insert if not)."""
        pass
