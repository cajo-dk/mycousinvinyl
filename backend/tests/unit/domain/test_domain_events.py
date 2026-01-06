"""
Unit tests for Domain Events.

Tests event creation, serialization, and business rules.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime

from app.domain.events import (
    ArtistCreated,
    ArtistUpdated,
    ArtistDeleted,
    AlbumCreated,
    AlbumUpdated,
    CollectionItemAdded,
    CollectionItemUpdated,
    CollectionItemRemoved,
)


class TestArtistEvents:
    """Test Artist domain events."""

    def test_artist_created_event(self):
        """Should create ArtistCreated event with all fields."""
        artist_id = uuid4()
        user_id = uuid4()

        event = ArtistCreated(
            artist_id=artist_id,
            name="The Beatles",
            artist_type="Group",
            created_by=user_id
        )

        assert event.artist_id == artist_id
        assert event.name == "The Beatles"
        assert event.artist_type == "Group"
        assert event.created_by == user_id
        assert event.event_type == "ArtistCreated"
        assert event.event_version == "1.0.0"
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_at, datetime)

    def test_artist_created_event_serialization(self):
        """Should serialize to dict correctly."""
        artist_id = uuid4()

        event = ArtistCreated(
            artist_id=artist_id,
            name="Bob Dylan",
            artist_type="Person",
            created_by=None
        )

        event_dict = event.to_dict()

        assert event_dict["event_type"] == "ArtistCreated"
        assert event_dict["event_version"] == "1.0.0"
        assert event_dict["artist_id"] == str(artist_id)
        assert event_dict["name"] == "Bob Dylan"
        assert event_dict["artist_type"] == "Person"
        assert event_dict["created_by"] is None
        assert "event_id" in event_dict
        assert "occurred_at" in event_dict

    def test_artist_updated_event(self):
        """Should create ArtistUpdated event."""
        artist_id = uuid4()
        updates = {"name": "New Name", "country": "US"}

        event = ArtistUpdated(
            artist_id=artist_id,
            updated_fields=updates
        )

        assert event.artist_id == artist_id
        assert event.updated_fields == updates
        assert event.event_type == "ArtistUpdated"

    def test_artist_updated_event_serialization(self):
        """Should serialize updated fields correctly."""
        artist_id = uuid4()
        updates = {"name": "Updated", "bio": "New bio"}

        event = ArtistUpdated(
            artist_id=artist_id,
            updated_fields=updates
        )

        event_dict = event.to_dict()

        assert event_dict["artist_id"] == str(artist_id)
        assert event_dict["updated_fields"] == updates

    def test_artist_deleted_event(self):
        """Should create ArtistDeleted event."""
        artist_id = uuid4()

        event = ArtistDeleted(artist_id=artist_id)

        assert event.artist_id == artist_id
        assert event.event_type == "ArtistDeleted"

    def test_artist_deleted_event_serialization(self):
        """Should serialize deletion event."""
        artist_id = uuid4()

        event = ArtistDeleted(artist_id=artist_id)

        event_dict = event.to_dict()

        assert event_dict["artist_id"] == str(artist_id)
        assert event_dict["event_type"] == "ArtistDeleted"


class TestAlbumEvents:
    """Test Album domain events."""

    def test_album_created_event(self):
        """Should create AlbumCreated event."""
        album_id = uuid4()
        artist_id = uuid4()

        event = AlbumCreated(
            album_id=album_id,
            title="Abbey Road",
            artist_id=artist_id
        )

        assert event.album_id == album_id
        assert event.event_type == "AlbumCreated"

        payload = event._payload()
        assert payload["title"] == "Abbey Road"
        assert payload["artist_id"] == str(artist_id)

    def test_album_created_with_all_fields(self):
        """Should include all fields in payload."""
        album_id = uuid4()
        artist_id = uuid4()

        event = AlbumCreated(
            album_id=album_id,
            title="Dark Side of the Moon",
            artist_id=artist_id,
            release_type="Studio"
        )

        payload = event._payload()
        assert payload["title"] == "Dark Side of the Moon"
        assert payload["release_type"] == "Studio"

    def test_album_updated_event(self):
        """Should create AlbumUpdated event."""
        album_id = uuid4()

        event = AlbumUpdated(
            album_id=album_id,
            updated_fields={"title": "Updated Title", "label": "New Label"}
        )

        assert event.album_id == album_id
        assert event.event_type == "AlbumUpdated"

        payload = event._payload()
        assert payload["updated_fields"]["title"] == "Updated Title"
        assert payload["updated_fields"]["label"] == "New Label"


class TestCollectionEvents:
    """Test Collection domain events."""

    def test_collection_item_added_event(self):
        """Should create CollectionItemAdded event."""
        item_id = uuid4()
        user_id = uuid4()
        pressing_id = uuid4()

        event = CollectionItemAdded(
            collection_item_id=item_id,
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition="Mint",
            sleeve_condition="Near Mint"
        )

        assert event.collection_item_id == item_id
        assert event.event_type == "CollectionItemAdded"

        payload = event._payload()
        assert payload["user_id"] == str(user_id)
        assert payload["pressing_id"] == str(pressing_id)

    def test_collection_item_added_with_conditions(self):
        """Should include condition fields in payload."""
        item_id = uuid4()
        user_id = uuid4()
        pressing_id = uuid4()

        event = CollectionItemAdded(
            collection_item_id=item_id,
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition="Mint",
            sleeve_condition="Very Good Plus"
        )

        payload = event._payload()
        assert payload["media_condition"] == "Mint"
        assert payload["sleeve_condition"] == "Very Good Plus"

    def test_collection_item_updated_event(self):
        """Should create CollectionItemUpdated event."""
        item_id = uuid4()
        user_id = uuid4()

        event = CollectionItemUpdated(
            collection_item_id=item_id,
            user_id=user_id,
            updated_fields={"user_rating": 5}
        )

        assert event.collection_item_id == item_id
        assert event.event_type == "CollectionItemUpdated"

        payload = event._payload()
        assert payload["updated_fields"]["user_rating"] == 5

    def test_collection_item_removed_event(self):
        """Should create CollectionItemRemoved event."""
        item_id = uuid4()
        user_id = uuid4()
        pressing_id = uuid4()

        event = CollectionItemRemoved(
            collection_item_id=item_id,
            user_id=user_id,
            pressing_id=pressing_id
        )

        assert event.collection_item_id == item_id
        assert event.event_type == "CollectionItemRemoved"

        payload = event._payload()
        assert payload["user_id"] == str(user_id)
        assert payload["pressing_id"] == str(pressing_id)


class TestEventMetadata:
    """Test event metadata and common properties."""

    def test_event_has_unique_id(self):
        """Each event should have unique ID."""
        artist_id = uuid4()

        event1 = ArtistCreated(artist_id=artist_id, name="Artist 1", artist_type="Person")
        event2 = ArtistCreated(artist_id=artist_id, name="Artist 1", artist_type="Person")

        assert event1.event_id != event2.event_id

    def test_event_has_timestamp(self):
        """Event should have occurred_at timestamp."""
        event = ArtistCreated(
            artist_id=uuid4(),
            name="Test",
            artist_type="Person"
        )

        assert isinstance(event.occurred_at, datetime)
        assert event.occurred_at <= datetime.utcnow()

    def test_event_version(self):
        """Events should have version number."""
        event = ArtistCreated(
            artist_id=uuid4(),
            name="Test",
            artist_type="Person"
        )

        assert event.event_version == "1.0.0"

    def test_event_type_is_correct(self):
        """Event type should match event class name."""
        events_and_types = [
            (ArtistCreated(artist_id=uuid4(), name="Test", artist_type="Person"), "ArtistCreated"),
            (ArtistUpdated(artist_id=uuid4(), updated_fields={}), "ArtistUpdated"),
            (ArtistDeleted(artist_id=uuid4()), "ArtistDeleted"),
            (AlbumCreated(album_id=uuid4(), title="Test", artist_id=uuid4()), "AlbumCreated"),
        ]

        for event, expected_type in events_and_types:
            assert event.event_type == expected_type


class TestEventImmutability:
    """Test that events are immutable (frozen dataclasses)."""

    def test_cannot_modify_event_after_creation(self):
        """Should not be able to modify frozen event."""
        event = ArtistCreated(
            artist_id=uuid4(),
            name="Original Name",
            artist_type="Person"
        )

        # Frozen dataclasses should raise FrozenInstanceError
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            event.name = "Modified Name"

    def test_cannot_modify_event_id(self):
        """Should not be able to modify event ID."""
        event = ArtistCreated(
            artist_id=uuid4(),
            name="Test",
            artist_type="Person"
        )

        with pytest.raises(Exception):
            event.event_id = uuid4()

    def test_cannot_modify_timestamp(self):
        """Should not be able to modify timestamp."""
        event = ArtistCreated(
            artist_id=uuid4(),
            name="Test",
            artist_type="Person"
        )

        with pytest.raises(Exception):
            event.occurred_at = datetime.utcnow()


class TestEventSerialization:
    """Test event serialization for storage and messaging."""

    def test_serialized_event_has_all_required_fields(self):
        """Serialized event should have all required fields."""
        event = ArtistCreated(
            artist_id=uuid4(),
            name="Test Artist",
            artist_type="Person",
            created_by=uuid4()
        )

        serialized = event.to_dict()

        required_fields = ["event_id", "event_type", "event_version", "occurred_at"]
        for field in required_fields:
            assert field in serialized

    def test_serialized_uuids_are_strings(self):
        """UUIDs should be serialized as strings."""
        artist_id = uuid4()
        user_id = uuid4()

        event = ArtistCreated(
            artist_id=artist_id,
            name="Test",
            artist_type="Person",
            created_by=user_id
        )

        serialized = event.to_dict()

        assert isinstance(serialized["event_id"], str)
        assert isinstance(serialized["artist_id"], str)
        assert isinstance(serialized["created_by"], str)

    def test_serialized_datetime_is_isoformat(self):
        """Datetime should be serialized as ISO format string."""
        event = ArtistCreated(
            artist_id=uuid4(),
            name="Test",
            artist_type="Person"
        )

        serialized = event.to_dict()

        # Should be ISO format string
        assert isinstance(serialized["occurred_at"], str)
        # Should be parseable back to datetime
        datetime.fromisoformat(serialized["occurred_at"])

    def test_none_values_are_preserved(self):
        """None values should be preserved in serialization."""
        event = ArtistCreated(
            artist_id=uuid4(),
            name="Test",
            artist_type="Person",
            created_by=None
        )

        serialized = event.to_dict()

        assert "created_by" in serialized
        assert serialized["created_by"] is None


class TestEventEquality:
    """Test event equality and comparison."""

    def test_same_event_data_different_objects(self):
        """Events with same data should not be equal (different IDs and timestamps)."""
        artist_id = uuid4()

        event1 = ArtistCreated(artist_id=artist_id, name="Test", artist_type="Person")
        event2 = ArtistCreated(artist_id=artist_id, name="Test", artist_type="Person")

        # Different event IDs and timestamps make them unique
        assert event1 != event2
        assert event1.event_id != event2.event_id
