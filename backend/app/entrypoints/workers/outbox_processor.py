"""
Outbox processor worker.

This worker:
- Polls the outbox table for unprocessed events
- Publishes events to ActiveMQ
- Marks events as processed
- Implements the transactional outbox pattern
"""

import asyncio
import logging
from uuid import UUID

from app.config import get_settings
from app.logging_config import configure_logging
from app.adapters.postgres.database import AsyncSessionLocal
from app.adapters.postgres.unit_of_work import SqlAlchemyUnitOfWork
from app.adapters.messaging.publisher_factory import get_message_publisher

configure_logging(get_settings().log_level)
logger = logging.getLogger(__name__)


class OutboxProcessor:
    """Processes outbox events and publishes them to ActiveMQ."""

    def __init__(self):
        self.settings = get_settings()
        self.publisher = get_message_publisher()
        self.running = False

    async def process_events(self):
        """Process a batch of outbox events."""
        async with AsyncSessionLocal() as session:
            uow = SqlAlchemyUnitOfWork(session)

            try:
                # Get unprocessed events
                events = await uow.outbox_repository.get_unprocessed_events(limit=100)

                if not events:
                    return 0

                logger.info(f"Processing {len(events)} outbox events...")

                processed_count = 0
                for event in events:
                    try:
                        logger.debug(
                            "Outbox event payload: type=%s id=%s destination=%s headers=%s metadata=%s payload=%s",
                            event.get('event_type'),
                            event.get('id'),
                            event.get('destination'),
                            event.get('headers'),
                            event.get('metadata'),
                            event.get('payload'),
                        )
                        # Publish to ActiveMQ
                        await self.publisher.publish(
                            destination=event['destination'],
                            message=event['payload'],
                            headers=event.get('headers', {})
                        )

                        # Mark as processed
                        await uow.outbox_repository.mark_as_processed(event['id'])
                        await uow.commit()

                        processed_count += 1
                        logger.info(f"Processed event {event['event_type']} ({event['id']})")

                    except Exception as e:
                        logger.error(f"Error processing event {event['id']}: {e}", exc_info=True)
                        await uow.rollback()
                        continue

                return processed_count

            except Exception as e:
                logger.error(f"Error in outbox processor: {e}", exc_info=True)
                await uow.rollback()
                return 0

    async def cleanup_old_events(self):
        """Clean up old processed events."""
        async with AsyncSessionLocal() as session:
            uow = SqlAlchemyUnitOfWork(session)

            try:
                deleted_count = await uow.outbox_repository.delete_processed_events(older_than_days=7)
                await uow.commit()

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old processed events")

            except Exception as e:
                logger.error(f"Error cleaning up old events: {e}", exc_info=True)
                await uow.rollback()

    async def run(self):
        """Main processing loop."""
        self.running = True
        logger.info("Outbox processor started")

        cleanup_counter = 0

        try:
            while self.running:
                # Process events
                processed = await self.process_events()

                # Run cleanup every 100 iterations (approximately every 10 minutes if processing every 6 seconds)
                cleanup_counter += 1
                if cleanup_counter >= 100:
                    await self.cleanup_old_events()
                    cleanup_counter = 0

                # Wait before next iteration
                # If we processed events, check again sooner; otherwise wait longer
                wait_time = 1 if processed > 0 else 5
                await asyncio.sleep(wait_time)

        except Exception as e:
            logger.error(f"Fatal error in outbox processor: {e}", exc_info=True)
            raise
        finally:
            self.publisher.disconnect()
            logger.info("Outbox processor stopped")

    def stop(self):
        """Stop the processor."""
        self.running = False


async def main():
    """Start the outbox processor."""
    processor = OutboxProcessor()

    try:
        await processor.run()
    except KeyboardInterrupt:
        logger.info("Shutting down outbox processor...")
        processor.stop()


if __name__ == "__main__":
    asyncio.run(main())
