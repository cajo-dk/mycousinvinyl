"""
Outbox repository port interface.

Manages outbox events for the transactional outbox pattern.
"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.domain.events import DomainEvent


class OutboxRepository(ABC):
    """
    Repository for managing outbox events.

    The outbox pattern ensures that domain events are reliably published
    by storing them in the database as part of the same transaction that
    performs the business operation.
    """

    @abstractmethod
    async def add_event(
        self,
        event: DomainEvent,
        aggregate_id: UUID,
        aggregate_type: str,
        destination: str
    ) -> None:
        """
        Add a domain event to the outbox.

        Args:
            event: The domain event to store
            aggregate_id: ID of the aggregate that raised the event
            aggregate_type: Type of the aggregate (e.g., 'Artist', 'Album')
            destination: ActiveMQ destination (e.g., '/topic/artist.created')
        """
        pass

    @abstractmethod
    async def get_unprocessed_events(self, limit: int = 100) -> List[dict]:
        """
        Get unprocessed events from the outbox.

        Args:
            limit: Maximum number of events to retrieve

        Returns:
            List of unprocessed outbox events as dictionaries
        """
        pass

    @abstractmethod
    async def mark_as_processed(self, event_id: UUID) -> None:
        """
        Mark an event as processed.

        Args:
            event_id: ID of the event to mark as processed
        """
        pass

    @abstractmethod
    async def delete_processed_events(self, older_than_days: int = 7) -> int:
        """
        Delete processed events older than a certain number of days.

        Args:
            older_than_days: Delete events processed more than this many days ago

        Returns:
            Number of events deleted
        """
        pass
