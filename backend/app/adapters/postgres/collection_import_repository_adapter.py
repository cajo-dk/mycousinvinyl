"""Collection import repository PostgreSQL adapter."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.collection_import_repository import CollectionImportRepository
from app.domain.entities import CollectionImport, CollectionImportRow
from app.adapters.postgres.models import CollectionImportModel, CollectionImportRowModel


class CollectionImportRepositoryAdapter(CollectionImportRepository):
    """PostgreSQL implementation of CollectionImportRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_import(self, import_job: CollectionImport) -> CollectionImport:
        model = CollectionImportModel.from_domain(import_job)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get_import(self, import_id: UUID, user_id: UUID) -> Optional[CollectionImport]:
        result = await self.session.execute(
            select(CollectionImportModel).where(
                CollectionImportModel.id == import_id,
                CollectionImportModel.user_id == user_id
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def update_import(self, import_job: CollectionImport) -> CollectionImport:
        result = await self.session.execute(
            select(CollectionImportModel).where(CollectionImportModel.id == import_job.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Import job {import_job.id} not found")

        model.status = import_job.status
        model.total_rows = import_job.total_rows
        model.processed_rows = import_job.processed_rows
        model.success_count = import_job.success_count
        model.error_count = import_job.error_count
        model.started_at = import_job.started_at
        model.completed_at = import_job.completed_at
        model.error_summary = import_job.error_summary
        model.options = import_job.options

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def add_rows(self, rows: List[CollectionImportRow]) -> None:
        for row in rows:
            self.session.add(CollectionImportRowModel.from_domain(row))
        await self.session.flush()

    async def get_pending_rows(self, import_id: UUID, limit: int = 100) -> List[CollectionImportRow]:
        result = await self.session.execute(
            select(CollectionImportRowModel)
            .where(
                CollectionImportRowModel.import_id == import_id,
                CollectionImportRowModel.status == 'pending'
            )
            .order_by(CollectionImportRowModel.row_number)
            .limit(limit)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def update_row(self, row: CollectionImportRow) -> CollectionImportRow:
        result = await self.session.execute(
            select(CollectionImportRowModel).where(CollectionImportRowModel.id == row.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Import row {row.id} not found")

        model.status = row.status
        model.raw_data = row.raw_data
        model.discogs_release_id = row.discogs_release_id
        model.artist_id = row.artist_id
        model.album_id = row.album_id
        model.pressing_id = row.pressing_id
        model.collection_item_id = row.collection_item_id
        model.error_message = row.error_message

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get_rows(
        self,
        import_id: UUID,
        user_id: UUID,
        limit: int = 500,
    ) -> List[CollectionImportRow]:
        result = await self.session.execute(
            select(CollectionImportRowModel)
            .join(
                CollectionImportModel,
                CollectionImportRowModel.import_id == CollectionImportModel.id,
            )
            .where(
                CollectionImportRowModel.import_id == import_id,
                CollectionImportModel.user_id == user_id,
            )
            .order_by(CollectionImportRowModel.row_number)
            .limit(limit)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]
