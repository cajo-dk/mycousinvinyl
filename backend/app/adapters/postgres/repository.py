"""
SQLAlchemy repository implementations.
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repository import ExampleRepository
from app.domain.entities import ExampleEntity
from app.adapters.postgres.models import ExampleModel


class SqlAlchemyExampleRepository(ExampleRepository):
    """SQLAlchemy implementation of ExampleRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, entity: ExampleEntity) -> None:
        """Add a new entity."""
        model = ExampleModel.from_domain(entity)
        self.session.add(model)

    async def get(self, entity_id: UUID) -> Optional[ExampleEntity]:
        """Get entity by ID."""
        result = await self.session.execute(
            select(ExampleModel).where(ExampleModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ExampleEntity]:
        """Get all entities with pagination."""
        result = await self.session.execute(
            select(ExampleModel).limit(limit).offset(offset)
        )
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def update(self, entity: ExampleEntity) -> None:
        """Update an existing entity."""
        result = await self.session.execute(
            select(ExampleModel).where(ExampleModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.name = entity.name
            model.description = entity.description
            model.updated_at = entity.updated_at

    async def delete(self, entity_id: UUID) -> None:
        """Delete an entity."""
        result = await self.session.execute(
            select(ExampleModel).where(ExampleModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
