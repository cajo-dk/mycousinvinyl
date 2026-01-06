"""
Message Publisher port interface.

Defines the contract for publishing integration events to the message broker.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class MessagePublisher(ABC):
    """Message publisher interface for integration events."""

    @abstractmethod
    async def publish(
        self,
        destination: str,
        message: Dict[str, Any],
        headers: Dict[str, str] = None,
    ) -> None:
        """
        Publish a message to the specified destination.

        Args:
            destination: Queue or topic name
            message: Message payload
            headers: Optional message headers
        """
        pass
