"""
SQLAlchemy outbox repository implementation.
"""

from datetime import datetime, timedelta
from typing import List
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.outbox_repository import OutboxRepository
from app.adapters.postgres.models import OutboxEventModel
from app.domain.events import DomainEvent


class OutboxRepositoryAdapter(OutboxRepository):
    """SQLAlchemy implementation of outbox repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_event(
        self,
        event: DomainEvent,
        aggregate_id: UUID,
        aggregate_type: str,
        destination: str
    ) -> None:
        """Add a domain event to the outbox."""
        outbox_event = OutboxEventModel(
            event_type=event.event_type,
            event_version=event.event_version,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            destination=destination,
            payload=event.to_dict(),
            headers={},
            event_metadata={
                'occurred_at': event.occurred_at.isoformat()
            },
            created_at=datetime.utcnow(),
            processed=False
        )

        self.session.add(outbox_event)

    async def get_unprocessed_events(self, limit: int = 100) -> List[dict]:
        """Get unprocessed events from the outbox."""
        stmt = (
            select(OutboxEventModel)
            .where(OutboxEventModel.processed == False)
            .order_by(OutboxEventModel.created_at)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        events = result.scalars().all()

        return [
            {
                'id': event.id,
                'event_type': event.event_type,
                'event_version': event.event_version,
                'aggregate_id': event.aggregate_id,
                'aggregate_type': event.aggregate_type,
                'destination': event.destination,
                'payload': event.payload,
                'headers': event.headers,
                'metadata': event.event_metadata,
                'created_at': event.created_at
            }
            for event in events
        ]

    async def mark_as_processed(self, event_id: UUID) -> None:
        """Mark an event as processed."""
        stmt = (
            update(OutboxEventModel)
            .where(OutboxEventModel.id == event_id)
            .values(processed=True, processed_at=datetime.utcnow())
        )

        await self.session.execute(stmt)

    async def delete_processed_events(self, older_than_days: int = 7) -> int:
        """Delete processed events older than a certain number of days."""
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        stmt = (
            delete(OutboxEventModel)
            .where(OutboxEventModel.processed == True)
            .where(OutboxEventModel.processed_at < cutoff_date)
        )

        result = await self.session.execute(stmt)
        return result.rowcount
