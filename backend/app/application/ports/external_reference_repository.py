"""External reference repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.entities import ExternalReference
from app.domain.value_objects import ExternalSource


class ExternalReferenceRepository(ABC):
    """Repository interface for ExternalReference entities."""

    @abstractmethod
    async def add(self, reference: ExternalReference) -> ExternalReference:
        """Add a new external reference."""
        pass

    @abstractmethod
    async def get(self, reference_id: UUID) -> Optional[ExternalReference]:
        """Get external reference by ID."""
        pass

    @abstractmethod
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID
    ) -> List[ExternalReference]:
        """Get all external references for an entity."""
        pass

    @abstractmethod
    async def get_by_entity_and_source(
        self,
        entity_type: str,
        entity_id: UUID,
        source: ExternalSource
    ) -> Optional[ExternalReference]:
        """Get external reference for an entity and specific source."""
        pass

    @abstractmethod
    async def update(self, reference: ExternalReference) -> ExternalReference:
        """Update external reference."""
        pass

    @abstractmethod
    async def delete(self, reference_id: UUID) -> None:
        """Delete external reference."""
        pass

    @abstractmethod
    async def upsert(self, reference: ExternalReference) -> ExternalReference:
        """Upsert external reference (update if exists, insert if not)."""
        pass
