"""System log repository port interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple

from app.domain.entities import SystemLogEntry


class SystemLogRepository(ABC):
    """Repository interface for system log entries."""

    @abstractmethod
    async def create(self, entry: SystemLogEntry) -> SystemLogEntry:
        """Create a new log entry."""
        raise NotImplementedError

    @abstractmethod
    async def list(self, limit: int, offset: int) -> Tuple[List[SystemLogEntry], int]:
        """List log entries with pagination."""
        raise NotImplementedError

    @abstractmethod
    async def delete_older_than(self, cutoff: datetime) -> int:
        """Delete log entries older than cutoff."""
        raise NotImplementedError
