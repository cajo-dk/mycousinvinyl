"""Matrix repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.entities import Matrix


class MatrixRepository(ABC):
    """Repository interface for Matrix (runout code) entities."""

    @abstractmethod
    async def add(self, matrix: Matrix) -> Matrix:
        """Add a new matrix code."""
        pass

    @abstractmethod
    async def get(self, matrix_id: UUID) -> Optional[Matrix]:
        """Get matrix by ID."""
        pass

    @abstractmethod
    async def get_by_pressing(self, pressing_id: UUID) -> List[Matrix]:
        """Get all matrix codes for a pressing, sorted by side."""
        pass

    @abstractmethod
    async def get_by_pressing_and_side(self, pressing_id: UUID, side: str) -> Optional[Matrix]:
        """Get matrix code for a specific pressing side."""
        pass

    @abstractmethod
    async def update(self, matrix: Matrix) -> Matrix:
        """Update matrix code."""
        pass

    @abstractmethod
    async def delete(self, matrix_id: UUID) -> None:
        """Delete matrix code."""
        pass

    @abstractmethod
    async def bulk_upsert(self, pressing_id: UUID, matrices: List[Matrix]) -> List[Matrix]:
        """Bulk upsert matrix codes for a pressing (update or insert)."""
        pass
