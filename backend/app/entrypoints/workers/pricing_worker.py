"""
Pricing worker for marketplace price updates.

This worker:
- Runs every 5 minutes
- Fetches stale pricing data (older than 30 days)
- Updates market_data table with Discogs marketplace pricing
- Prioritizes pressings in user collections
- Rate limits to 1 request/second (60/min with OAuth)
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.logging_config import configure_logging
from app.adapters.postgres.system_log_repository_adapter import SystemLogRepositoryAdapter
from app.domain.entities import SystemLogEntry
from app.adapters.postgres.database import AsyncSessionLocal
from app.adapters.postgres.market_data_repository_adapter import MarketDataRepositoryAdapter
from app.adapters.postgres.pressing_repository_adapter import PressingRepositoryAdapter
from app.adapters.postgres.system_log_repository_adapter import SystemLogRepositoryAdapter
from app.adapters.http.discogs_client import DiscogsClientAdapter
from app.application.services.pricing_service import PricingService

configure_logging(get_settings().log_level)
logger = logging.getLogger(__name__)


class PricingWorker:
    """Updates marketplace pricing data from Discogs."""

    def __init__(self):
        self.settings = get_settings()
        self.running = False
        self.stale_threshold_days = 30
        self.batch_size = 300  # Max pressings to process per run
        self.rate_limit_seconds = 1  # 1 request per second (well under 60/min OAuth limit)
        self.run_interval_seconds = 300  # Run every 5 minutes

    async def process_batch(self):
        """Process a batch of stale pricing data."""
        async with AsyncSessionLocal() as session:
            # Create repositories and services
            market_data_repo = MarketDataRepositoryAdapter(session)
            pressing_repo = PressingRepositoryAdapter(session)
            log_repo = SystemLogRepositoryAdapter(session)
            discogs_client = DiscogsClientAdapter(
                base_url=self.settings.discogs_service_url,
                timeout_seconds=10.0
            )
            pricing_service = PricingService(
                discogs_client=discogs_client,
                market_data_repo=market_data_repo,
                pressing_repo=pressing_repo
            )

            try:
                # Get stale pressings (older than threshold)
                # Use timezone-aware datetime but convert to naive for database compatibility
                stale_threshold = (datetime.now(timezone.utc) - timedelta(days=self.stale_threshold_days)).replace(tzinfo=None)
                stale_pressings = await market_data_repo.get_stale_pressings(
                    older_than=stale_threshold,
                    limit=self.batch_size
                )

                if not stale_pressings:
                    logger.info("No stale pricing data to update")
                    return 0

                logger.info(
                    f"Found {len(stale_pressings)} pressings with stale pricing "
                    f"(older than {self.stale_threshold_days} days)"
                )

                updated_count = 0
                unavailable_count = 0
                error_count = 0

                for pressing_data in stale_pressings:
                    pressing_id = pressing_data["pressing_id"]
                    discogs_release_id = pressing_data["discogs_release_id"]
                    in_collection = pressing_data["in_collection"]

                    try:
                        logger.info(
                            f"Fetching pricing for pressing {pressing_id} "
                            f"(Discogs release {discogs_release_id}) "
                            f"{'[IN COLLECTION]' if in_collection else '[NOT IN COLLECTION]'}"
                        )

                        # Fetch and update pricing
                        result = await pricing_service.fetch_and_update_pricing(pressing_id)

                        if result:
                            updated_count += 1
                            logger.info(
                                f"Updated pricing for pressing {pressing_id}: "
                                f"{result['currency']} {result['median_value']} "
                                f"(min: {result['min_value']}, max: {result['max_value']})"
                            )
                        else:
                            unavailable_count += 1
                            logger.info(
                                f"No pricing available for pressing {pressing_id} "
                                f"(Discogs release {discogs_release_id})"
                            )

                        # Rate limiting: wait 1 second between requests
                        await asyncio.sleep(self.rate_limit_seconds)

                    except Exception as e:
                        error_count += 1
                        logger.error(
                            f"Error fetching pricing for pressing {pressing_id} "
                            f"(Discogs release {discogs_release_id}): {e}",
                            exc_info=True
                        )
                        # Continue to next pressing on error
                        continue

                logger.info(
                    f"Pricing batch complete: {updated_count} updated, "
                    f"{unavailable_count} unavailable, {error_count} errors"
                )
                await log_repo.create(SystemLogEntry(
                    user_id=None,
                    user_name="*system",
                    severity="INFO",
                    component="Pricing",
                    message=(
                        "Pricing batch complete: "
                        f"updated={updated_count}, "
                        f"unavailable={unavailable_count}, "
                        f"errors={error_count}"
                    ),
                ))
                await session.commit()

                return updated_count

            except Exception as e:
                logger.error(f"Error in pricing worker batch: {e}", exc_info=True)
                await log_repo.create(SystemLogEntry(
                    user_id=None,
                    user_name="*system",
                    severity="ERROR",
                    component="Pricing",
                    message=f"Pricing worker batch failed: {e}",
                ))
                await session.commit()
                return 0

    async def run(self):
        """Main processing loop."""
        self.running = True
        logger.info(
            f"Pricing worker started (run interval: {self.run_interval_seconds}s, "
            f"stale threshold: {self.stale_threshold_days} days, "
            f"batch size: {self.batch_size}, "
            f"rate limit: {self.rate_limit_seconds}s per request)"
        )

        try:
            while self.running:
                # Process batch
                updated = await self.process_batch()

                # Wait before next run
                logger.info(f"Waiting {self.run_interval_seconds}s until next run...")
                await asyncio.sleep(self.run_interval_seconds)

        except Exception as e:
            logger.error(f"Fatal error in pricing worker: {e}", exc_info=True)
            raise
        finally:
            logger.info("Pricing worker stopped")

    def stop(self):
        """Stop the worker."""
        self.running = False


async def main():
    """Start the pricing worker."""
    worker = PricingWorker()

    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Shutting down pricing worker...")
        worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
