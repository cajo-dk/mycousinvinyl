"""
Repository port interfaces.

These define the contract that database adapters must implement.
The application layer depends on these abstractions, not concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.entities import ExampleEntity


class ExampleRepository(ABC):
    """Repository interface for ExampleEntity."""

    @abstractmethod
    async def add(self, entity: ExampleEntity) -> None:
        """Add a new entity."""
        pass

    @abstractmethod
    async def get(self, entity_id: UUID) -> Optional[ExampleEntity]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ExampleEntity]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    async def update(self, entity: ExampleEntity) -> None:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> None:
        """Delete an entity."""
        pass
