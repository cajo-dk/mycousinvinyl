"""Collection import repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.entities import CollectionImport, CollectionImportRow


class CollectionImportRepository(ABC):
    """Repository interface for collection import jobs and rows."""

    @abstractmethod
    async def create_import(self, import_job: CollectionImport) -> CollectionImport:
        """Create a new import job."""
        pass

    @abstractmethod
    async def get_import(self, import_id: UUID, user_id: UUID) -> Optional[CollectionImport]:
        """Get an import job by ID (user-scoped)."""
        pass

    @abstractmethod
    async def update_import(self, import_job: CollectionImport) -> CollectionImport:
        """Update an import job."""
        pass

    @abstractmethod
    async def add_rows(self, rows: List[CollectionImportRow]) -> None:
        """Add import rows."""
        pass

    @abstractmethod
    async def get_pending_rows(self, import_id: UUID, limit: int = 100) -> List[CollectionImportRow]:
        """Fetch pending rows for processing."""
        pass

    @abstractmethod
    async def update_row(self, row: CollectionImportRow) -> CollectionImportRow:
        """Update an import row."""
        pass

    @abstractmethod
    async def get_rows(
        self,
        import_id: UUID,
        user_id: UUID,
        limit: int = 500,
    ) -> List[CollectionImportRow]:
        """Fetch rows for an import (user-scoped)."""
        pass
