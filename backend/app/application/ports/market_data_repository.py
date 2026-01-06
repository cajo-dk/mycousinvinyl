"""Port interface for market data repository."""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class MarketDataRepository(ABC):
    """Repository for market pricing data."""

    @abstractmethod
    async def get_by_pressing_id(self, pressing_id: UUID) -> Optional[dict]:
        """Get market data for a pressing."""
        pass

    @abstractmethod
    async def upsert(
        self,
        pressing_id: UUID,
        min_value: float,
        median_value: float,
        max_value: float,
        currency: str,
        last_sold_price: Optional[float] = None,
        availability_status: Optional[str] = None
    ) -> dict:
        """Insert or update market data for a pressing."""
        pass

    @abstractmethod
    async def get_stale_pressings(
        self,
        older_than: datetime,
        limit: int = 100
    ) -> List[dict]:
        """
        Get pressings with stale or missing market data.

        Returns pressings that:
        - Have no market data, OR
        - Have market data older than specified datetime
        - Have a discogs_release_id (required for pricing lookup)

        Prioritizes pressings in user collections.
        """
        pass

    @abstractmethod
    async def mark_pricing_unavailable(self, pressing_id: UUID) -> None:
        """
        Mark that pricing is unavailable for this pressing.

        Creates a market_data record with NULL values and current timestamp
        to prevent repeated failed lookups.
        """
        pass
