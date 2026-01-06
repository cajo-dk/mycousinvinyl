"""
Example application service.

Use-case orchestration lives here. This layer:
- Coordinates domain entities and adapters
- Manages transactions via Unit of Work
- Publishes integration events
- Is security-agnostic (no auth logic)
"""

from uuid import UUID
from typing import Optional, List

from app.domain.entities import ExampleEntity
from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.message_publisher import MessagePublisher


class ExampleService:
    """Service for example business operations."""

    def __init__(self, uow: UnitOfWork, publisher: MessagePublisher):
        self.uow = uow
        self.publisher = publisher

    async def create_example(self, name: str, description: Optional[str] = None) -> ExampleEntity:
        """
        Create a new example entity.

        This is a use-case that orchestrates:
        1. Entity creation
        2. Persistence
        3. Event publishing
        """
        # Create domain entity (business rules enforced here)
        entity = ExampleEntity(name=name, description=description)

        # Persist within transaction
        async with self.uow:
            await self.uow.example_repository.add(entity)
            await self.uow.commit()

        # Publish integration event
        await self.publisher.publish(
            destination="/topic/example.created",
            message={
                "id": str(entity.id),
                "name": entity.name,
                "created_at": entity.created_at.isoformat(),
            },
        )

        return entity

    async def get_example(self, entity_id: UUID) -> Optional[ExampleEntity]:
        """Get an example entity by ID."""
        async with self.uow:
            return await self.uow.example_repository.get(entity_id)

    async def list_examples(self, limit: int = 100, offset: int = 0) -> List[ExampleEntity]:
        """List all example entities with pagination."""
        async with self.uow:
            return await self.uow.example_repository.get_all(limit=limit, offset=offset)

    async def update_example(self, entity_id: UUID, name: str) -> Optional[ExampleEntity]:
        """Update an example entity."""
        async with self.uow:
            entity = await self.uow.example_repository.get(entity_id)
            if not entity:
                return None

            # Business logic in domain entity
            entity.update_name(name)

            await self.uow.example_repository.update(entity)
            await self.uow.commit()

        # Publish integration event
        await self.publisher.publish(
            destination="/topic/example.updated",
            message={
                "id": str(entity.id),
                "name": entity.name,
                "updated_at": entity.updated_at.isoformat(),
            },
        )

        return entity

    async def delete_example(self, entity_id: UUID) -> bool:
        """Delete an example entity."""
        async with self.uow:
            entity = await self.uow.example_repository.get(entity_id)
            if not entity:
                return False

            await self.uow.example_repository.delete(entity_id)
            await self.uow.commit()

        # Publish integration event
        await self.publisher.publish(
            destination="/topic/example.deleted",
            message={"id": str(entity_id)},
        )

        return True
