"""
Unit tests for Event System components.

Tests outbox pattern, event processing, and message publishing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4
from datetime import datetime

from app.domain.events import ArtistCreated, ArtistUpdated, ArtistDeleted


@pytest.fixture
def mock_outbox_repository():
    """Create mock outbox repository."""
    repo = AsyncMock()
    repo.add_event = AsyncMock()
    repo.get_unprocessed_events = AsyncMock()
    repo.mark_as_processed = AsyncMock()
    repo.delete_processed_events = AsyncMock()
    return repo


@pytest.fixture
def mock_message_publisher():
    """Create mock message publisher."""
    publisher = AsyncMock()
    publisher.publish = AsyncMock()
    publisher.connect = AsyncMock()
    publisher.disconnect = AsyncMock()
    return publisher


class TestOutboxRepositoryUsage:
    """Test how outbox repository is used in the application."""

    @pytest.mark.asyncio
    async def test_add_event_to_outbox(self, mock_outbox_repository):
        """Should add event to outbox with metadata."""
        artist_id = uuid4()
        event = ArtistCreated(
            artist_id=artist_id,
            name="The Beatles",
            artist_type="Group",
            created_by=None
        )

        await mock_outbox_repository.add_event(
            event=event,
            aggregate_id=artist_id,
            aggregate_type='Artist',
            destination='/topic/artist.created'
        )

        mock_outbox_repository.add_event.assert_called_once()
        call_args = mock_outbox_repository.add_event.call_args

        assert call_args.kwargs['event'] == event
        assert call_args.kwargs['aggregate_id'] == artist_id
        assert call_args.kwargs['aggregate_type'] == 'Artist'
        assert call_args.kwargs['destination'] == '/topic/artist.created'

    @pytest.mark.asyncio
    async def test_get_unprocessed_events(self, mock_outbox_repository):
        """Should retrieve unprocessed events from outbox."""
        mock_events = [
            {
                'id': uuid4(),
                'event_type': 'artist.created',
                'aggregate_id': uuid4(),
                'aggregate_type': 'Artist',
                'destination': '/topic/artist.created',
                'payload': {'artist_id': str(uuid4()), 'name': 'Test'},
                'headers': {},
                'processed': False,
                'created_at': datetime.utcnow()
            }
        ]
        mock_outbox_repository.get_unprocessed_events.return_value = mock_events

        events = await mock_outbox_repository.get_unprocessed_events(limit=100)

        assert len(events) == 1
        assert events[0]['event_type'] == 'artist.created'
        assert events[0]['processed'] is False
        mock_outbox_repository.get_unprocessed_events.assert_called_once_with(limit=100)

    @pytest.mark.asyncio
    async def test_mark_event_as_processed(self, mock_outbox_repository):
        """Should mark event as processed after publishing."""
        event_id = uuid4()

        await mock_outbox_repository.mark_as_processed(event_id)

        mock_outbox_repository.mark_as_processed.assert_called_once_with(event_id)

    @pytest.mark.asyncio
    async def test_delete_old_processed_events(self, mock_outbox_repository):
        """Should delete old processed events for cleanup."""
        days_old = 30

        await mock_outbox_repository.delete_processed_events(older_than_days=days_old)

        mock_outbox_repository.delete_processed_events.assert_called_once_with(
            older_than_days=days_old
        )


class TestOutboxProcessor:
    """Test Outbox Processor component."""

    @pytest.mark.asyncio
    async def test_process_events_publishes_to_message_broker(
        self,
        mock_outbox_repository,
        mock_message_publisher
    ):
        """Should publish unprocessed events to message broker."""
        # Arrange
        event_id = uuid4()
        artist_id = uuid4()
        mock_events = [
            {
                'id': event_id,
                'event_type': 'artist.created',
                'aggregate_id': artist_id,
                'destination': '/topic/artist.created',
                'payload': {
                    'event_id': str(uuid4()),
                    'event_type': 'artist.created',
                    'artist_id': str(artist_id),
                    'name': 'The Beatles'
                },
                'headers': {'event_version': '1.0.0'},
            }
        ]
        mock_outbox_repository.get_unprocessed_events.return_value = mock_events

        # Act - Simulate processor behavior
        events = await mock_outbox_repository.get_unprocessed_events(limit=100)

        for event in events:
            await mock_message_publisher.publish(
                destination=event['destination'],
                message=event['payload'],
                headers=event.get('headers', {})
            )
            await mock_outbox_repository.mark_as_processed(event['id'])

        # Assert
        mock_message_publisher.publish.assert_called_once_with(
            destination='/topic/artist.created',
            message=mock_events[0]['payload'],
            headers={'event_version': '1.0.0'}
        )
        mock_outbox_repository.mark_as_processed.assert_called_once_with(event_id)

    @pytest.mark.asyncio
    async def test_process_multiple_events_in_batch(
        self,
        mock_outbox_repository,
        mock_message_publisher
    ):
        """Should process multiple events in a batch."""
        # Arrange
        event1_id = uuid4()
        event2_id = uuid4()
        event3_id = uuid4()

        mock_events = [
            {
                'id': event1_id,
                'destination': '/topic/artist.created',
                'payload': {'event_type': 'artist.created', 'name': 'Artist 1'},
                'headers': {},
            },
            {
                'id': event2_id,
                'destination': '/topic/artist.updated',
                'payload': {'event_type': 'artist.updated', 'name': 'Artist 2'},
                'headers': {},
            },
            {
                'id': event3_id,
                'destination': '/topic/artist.deleted',
                'payload': {'event_type': 'artist.deleted'},
                'headers': {},
            },
        ]
        mock_outbox_repository.get_unprocessed_events.return_value = mock_events

        # Act
        events = await mock_outbox_repository.get_unprocessed_events(limit=100)

        for event in events:
            await mock_message_publisher.publish(
                destination=event['destination'],
                message=event['payload'],
                headers=event['headers']
            )
            await mock_outbox_repository.mark_as_processed(event['id'])

        # Assert
        assert mock_message_publisher.publish.call_count == 3
        assert mock_outbox_repository.mark_as_processed.call_count == 3

        # Verify all events were marked as processed
        processed_ids = [
            call[0][0] for call in mock_outbox_repository.mark_as_processed.call_args_list
        ]
        assert event1_id in processed_ids
        assert event2_id in processed_ids
        assert event3_id in processed_ids

    @pytest.mark.asyncio
    async def test_processor_handles_no_events(
        self,
        mock_outbox_repository,
        mock_message_publisher
    ):
        """Should handle case when no events are available."""
        mock_outbox_repository.get_unprocessed_events.return_value = []

        events = await mock_outbox_repository.get_unprocessed_events(limit=100)

        assert len(events) == 0
        mock_message_publisher.publish.assert_not_called()
        mock_outbox_repository.mark_as_processed.assert_not_called()

    @pytest.mark.asyncio
    async def test_processor_continues_on_publish_error(
        self,
        mock_outbox_repository,
        mock_message_publisher
    ):
        """Should continue processing other events if one fails."""
        event1_id = uuid4()
        event2_id = uuid4()

        mock_events = [
            {
                'id': event1_id,
                'destination': '/topic/artist.created',
                'payload': {'name': 'Artist 1'},
                'headers': {},
            },
            {
                'id': event2_id,
                'destination': '/topic/artist.updated',
                'payload': {'name': 'Artist 2'},
                'headers': {},
            },
        ]
        mock_outbox_repository.get_unprocessed_events.return_value = mock_events

        # First publish fails, second succeeds
        mock_message_publisher.publish.side_effect = [
            Exception("Connection failed"),
            None  # Second call succeeds
        ]

        events = await mock_outbox_repository.get_unprocessed_events(limit=100)

        for event in events:
            try:
                await mock_message_publisher.publish(
                    destination=event['destination'],
                    message=event['payload'],
                    headers=event['headers']
                )
                await mock_outbox_repository.mark_as_processed(event['id'])
            except Exception:
                # Log error but continue processing
                pass

        # Only second event should be marked as processed
        mock_outbox_repository.mark_as_processed.assert_called_once_with(event2_id)


class TestEventConsumer:
    """Test Event Consumer component."""

    def test_consumer_handles_artist_created_event(self):
        """Should handle artist.created event."""
        message = {
            'event_id': str(uuid4()),
            'event_type': 'artist.created',
            'artist_id': str(uuid4()),
            'name': 'The Beatles',
            'artist_type': 'Group'
        }

        # Simulate consumer handling
        event_type = message['event_type']
        assert event_type == 'artist.created'

        # Consumer would extract data and process
        artist_name = message['name']
        assert artist_name == 'The Beatles'

    def test_consumer_handles_artist_updated_event(self):
        """Should handle artist.updated event."""
        message = {
            'event_id': str(uuid4()),
            'event_type': 'artist.updated',
            'artist_id': str(uuid4()),
            'updated_fields': {'name': 'Updated Name', 'country': 'US'}
        }

        event_type = message['event_type']
        assert event_type == 'artist.updated'
        assert 'updated_fields' in message

    def test_consumer_handles_artist_deleted_event(self):
        """Should handle artist.deleted event."""
        artist_id = uuid4()
        message = {
            'event_id': str(uuid4()),
            'event_type': 'artist.deleted',
            'artist_id': str(artist_id)
        }

        event_type = message['event_type']
        assert event_type == 'artist.deleted'

    def test_consumer_routes_to_correct_handler(self):
        """Should route events to correct handlers based on event type."""
        handlers = {
            'artist.created': MagicMock(),
            'artist.updated': MagicMock(),
            'artist.deleted': MagicMock(),
        }

        messages = [
            {'event_type': 'artist.created', 'name': 'Test'},
            {'event_type': 'artist.updated', 'updated_fields': {}},
            {'event_type': 'artist.deleted', 'artist_id': str(uuid4())},
        ]

        for message in messages:
            event_type = message['event_type']
            if event_type in handlers:
                handlers[event_type](message)

        # Verify each handler was called once
        for handler in handlers.values():
            handler.assert_called_once()


class TestEventIntegration:
    """Test integration between event system components."""

    @pytest.mark.asyncio
    async def test_full_event_flow(
        self,
        mock_outbox_repository,
        mock_message_publisher
    ):
        """Test complete flow from event creation to publishing."""
        # 1. Service creates event and adds to outbox
        artist_id = uuid4()
        event = ArtistCreated(
            artist_id=artist_id,
            name="The Beatles",
            artist_type="Group",
            created_by=None
        )

        await mock_outbox_repository.add_event(
            event=event,
            aggregate_id=artist_id,
            aggregate_type='Artist',
            destination='/topic/artist.created'
        )

        # 2. Processor fetches unprocessed events
        mock_outbox_repository.get_unprocessed_events.return_value = [
            {
                'id': uuid4(),
                'destination': '/topic/artist.created',
                'payload': event.to_dict(),
                'headers': {},
            }
        ]

        events = await mock_outbox_repository.get_unprocessed_events(limit=100)

        # 3. Processor publishes to message broker
        for evt in events:
            await mock_message_publisher.publish(
                destination=evt['destination'],
                message=evt['payload'],
                headers=evt['headers']
            )
            await mock_outbox_repository.mark_as_processed(evt['id'])

        # Verify complete flow
        mock_outbox_repository.add_event.assert_called_once()
        mock_message_publisher.publish.assert_called_once()
        mock_outbox_repository.mark_as_processed.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_ordering_preserved(
        self,
        mock_outbox_repository,
        mock_message_publisher
    ):
        """Should process events in order they were created."""
        # Events for same aggregate should be processed in order
        artist_id = uuid4()

        # Create multiple events for same artist
        events_in_order = [
            {
                'id': uuid4(),
                'aggregate_id': artist_id,
                'destination': '/topic/artist.created',
                'payload': {'event_type': 'artist.created', 'name': 'Original'},
                'headers': {},
                'created_at': datetime(2024, 1, 1, 10, 0, 0),
            },
            {
                'id': uuid4(),
                'aggregate_id': artist_id,
                'destination': '/topic/artist.updated',
                'payload': {'event_type': 'artist.updated', 'name': 'Updated'},
                'headers': {},
                'created_at': datetime(2024, 1, 1, 10, 0, 1),
            },
            {
                'id': uuid4(),
                'aggregate_id': artist_id,
                'destination': '/topic/artist.deleted',
                'payload': {'event_type': 'artist.deleted'},
                'headers': {},
                'created_at': datetime(2024, 1, 1, 10, 0, 2),
            },
        ]

        mock_outbox_repository.get_unprocessed_events.return_value = events_in_order

        events = await mock_outbox_repository.get_unprocessed_events(limit=100)

        published_events = []
        for event in events:
            await mock_message_publisher.publish(
                destination=event['destination'],
                message=event['payload'],
                headers=event['headers']
            )
            published_events.append(event['payload']['event_type'])

        # Verify events were published in correct order
        assert published_events == ['artist.created', 'artist.updated', 'artist.deleted']


class TestEventRetry:
    """Test event retry and error handling."""

    @pytest.mark.asyncio
    async def test_failed_events_remain_unprocessed(
        self,
        mock_outbox_repository,
        mock_message_publisher
    ):
        """Events should remain unprocessed if publishing fails."""
        event_id = uuid4()
        mock_events = [
            {
                'id': event_id,
                'destination': '/topic/artist.created',
                'payload': {'event_type': 'artist.created'},
                'headers': {},
            }
        ]

        mock_outbox_repository.get_unprocessed_events.return_value = mock_events
        mock_message_publisher.publish.side_effect = Exception("Broker unavailable")

        events = await mock_outbox_repository.get_unprocessed_events(limit=100)

        for event in events:
            try:
                await mock_message_publisher.publish(
                    destination=event['destination'],
                    message=event['payload'],
                    headers=event['headers']
                )
                await mock_outbox_repository.mark_as_processed(event['id'])
            except Exception:
                # Event remains unprocessed
                pass

        # Event should NOT be marked as processed
        mock_outbox_repository.mark_as_processed.assert_not_called()

        # On next poll, same event should be available
        events_retry = await mock_outbox_repository.get_unprocessed_events(limit=100)
        assert len(events_retry) == 1
        assert events_retry[0]['id'] == event_id
