"""Service for marketplace pricing operations."""

import logging
from typing import Optional
from uuid import UUID

from app.application.ports.discogs_client import DiscogsClient
from app.application.ports.market_data_repository import MarketDataRepository
from app.application.ports.pressing_repository import PressingRepository

logger = logging.getLogger(__name__)


class PricingService:
    """Application service for marketplace pricing."""

    def __init__(
        self,
        discogs_client: DiscogsClient,
        market_data_repo: MarketDataRepository,
        pressing_repo: PressingRepository
    ):
        self._discogs = discogs_client
        self._market_data_repo = market_data_repo
        self._pressing_repo = pressing_repo

    async def fetch_and_update_pricing(self, pressing_id: UUID) -> Optional[dict]:
        """
        Fetch pricing from Discogs and update market_data.

        Returns updated market data or None if pricing unavailable.
        """
        # Get pressing to find discogs_release_id
        pressing = await self._pressing_repo.get(pressing_id)
        if not pressing or not pressing.discogs_release_id:
            logger.warning(f"Pressing {pressing_id} has no Discogs release ID")
            return None

        # Fetch pricing from Discogs
        try:
            pricing = await self._discogs.get_price_suggestions(pressing.discogs_release_id)
        except Exception as exc:
            logger.error(
                f"Failed to fetch pricing for pressing {pressing_id}, "
                f"release {pressing.discogs_release_id}: {exc}"
            )
            return None

        # No pricing available
        if pricing is None:
            logger.info(
                f"No marketplace pricing available for pressing {pressing_id}, "
                f"release {pressing.discogs_release_id}"
            )
            await self._market_data_repo.mark_pricing_unavailable(pressing_id)
            return None

        # Update market_data
        market_data = await self._market_data_repo.upsert(
            pressing_id=pressing_id,
            min_value=pricing["min_value"],
            median_value=pricing["median_value"],
            max_value=pricing["max_value"],
            currency=pricing["currency"]
        )

        logger.info(
            f"Updated pricing for pressing {pressing_id}: "
            f"{market_data['currency']} {market_data['median_value']}"
        )

        return market_data

    async def get_pricing_for_pressing(self, pressing_id: UUID) -> Optional[dict]:
        """Get current market data for a pressing."""
        return await self._market_data_repo.get_by_pressing_id(pressing_id)
