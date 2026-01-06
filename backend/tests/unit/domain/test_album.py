"""
Unit tests for Album domain entity.

Tests business rules and validation logic for the Album entity.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, date

from app.domain.entities import Album, AlbumCreated, AlbumUpdated
from app.domain.value_objects import ReleaseType, DataSource, VerificationStatus


class TestAlbumCreation:
    """Test album creation and validation."""

    def test_create_album_with_valid_data(self):
        """Should create album with valid data."""
        artist_id = uuid4()
        album = Album(
            title="Abbey Road",
            primary_artist_id=artist_id,
            release_type=ReleaseType.STUDIO,
            original_release_year=1969,
        )

        assert album.title == "Abbey Road"
        assert album.primary_artist_id == artist_id
        assert album.release_type == ReleaseType.STUDIO
        assert album.original_release_year == 1969
        assert isinstance(album.id, UUID)
        assert isinstance(album.created_at, datetime)
        assert album.data_source == DataSource.USER
        assert album.verification_status == VerificationStatus.UNVERIFIED

    def test_create_album_with_minimal_data(self):
        """Should create album with only required fields."""
        artist_id = uuid4()
        album = Album(
            title="Test Album",
            primary_artist_id=artist_id,
        )

        assert album.title == "Test Album"
        assert album.primary_artist_id == artist_id
        assert album.release_type == ReleaseType.STUDIO  # default

    def test_title_is_stripped(self):
        """Should strip whitespace from title."""
        artist_id = uuid4()
        album = Album(
            title="  Abbey Road  ",
            primary_artist_id=artist_id,
        )

        assert album.title == "Abbey Road"

    def test_empty_title_raises_error(self):
        """Should raise ValueError for empty title."""
        artist_id = uuid4()
        with pytest.raises(ValueError, match="Album title is required"):
            Album(title="", primary_artist_id=artist_id)

    def test_whitespace_only_title_raises_error(self):
        """Should raise ValueError for whitespace-only title."""
        artist_id = uuid4()
        with pytest.raises(ValueError, match="Album title is required"):
            Album(title="   ", primary_artist_id=artist_id)

    def test_missing_title_raises_error(self):
        """Should raise ValueError when title is not provided."""
        artist_id = uuid4()
        with pytest.raises(ValueError, match="Album title is required"):
            Album(primary_artist_id=artist_id)

    def test_missing_artist_raises_error(self):
        """Should raise ValueError when primary_artist_id is not provided."""
        with pytest.raises(ValueError, match="Primary artist is required"):
            Album(title="Abbey Road")

    def test_none_artist_raises_error(self):
        """Should raise ValueError when primary_artist_id is None."""
        with pytest.raises(ValueError, match="Primary artist is required"):
            Album(title="Abbey Road", primary_artist_id=None)

    def test_self_referencing_original_release_raises_error(self):
        """Should raise ValueError if album references itself as original."""
        album_id = uuid4()
        artist_id = uuid4()

        with pytest.raises(ValueError, match="Album cannot reference itself as original release"):
            Album(
                id=album_id,
                title="Reissue",
                primary_artist_id=artist_id,
                original_release_id=album_id,
            )

    def test_album_creation_emits_event(self):
        """Should emit AlbumCreated event on creation."""
        artist_id = uuid4()
        album = Album(
            title="Abbey Road",
            primary_artist_id=artist_id,
        )

        assert len(album.events) == 1
        event = album.events[0]
        assert isinstance(event, AlbumCreated)
        assert event.event_type == "album.created"
        assert event.aggregate_id == album.id
        assert event.payload["title"] == "Abbey Road"
        assert event.payload["primary_artist_id"] == str(artist_id)

    def test_genre_and_style_ids(self):
        """Should handle genre and style IDs."""
        artist_id = uuid4()
        genre_id_1 = uuid4()
        genre_id_2 = uuid4()
        style_id = uuid4()

        album = Album(
            title="Abbey Road",
            primary_artist_id=artist_id,
            genre_ids=[genre_id_1, genre_id_2],
            style_ids=[style_id],
        )

        assert len(album.genre_ids) == 2
        assert genre_id_1 in album.genre_ids
        assert len(album.style_ids) == 1


class TestAlbumUpdate:
    """Test album update method."""

    def test_update_title(self):
        """Should update album title."""
        artist_id = uuid4()
        album = Album(title="Original Title", primary_artist_id=artist_id)
        album.events.clear()  # Clear creation event

        album.update(title="New Title")

        assert album.title == "New Title"
        assert len(album.events) == 1
        assert isinstance(album.events[0], AlbumUpdated)

    def test_update_title_strips_whitespace(self):
        """Should strip whitespace from updated title."""
        artist_id = uuid4()
        album = Album(title="Original", primary_artist_id=artist_id)

        album.update(title="  New Title  ")

        assert album.title == "New Title"

    def test_update_empty_title_raises_error(self):
        """Should raise ValueError when updating to empty title."""
        artist_id = uuid4()
        album = Album(title="Original", primary_artist_id=artist_id)

        with pytest.raises(ValueError, match="Album title cannot be empty"):
            album.update(title="")

    def test_update_primary_artist(self):
        """Should update primary artist."""
        artist_id_1 = uuid4()
        artist_id_2 = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id_1)

        album.update(primary_artist_id=artist_id_2)

        assert album.primary_artist_id == artist_id_2

    def test_update_none_artist_raises_error(self):
        """Should raise ValueError when updating artist to None."""
        artist_id = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id)

        with pytest.raises(ValueError, match="Primary artist is required"):
            album.update(primary_artist_id=None)

    def test_update_original_release_id(self):
        """Should update original_release_id."""
        artist_id = uuid4()
        original_album_id = uuid4()
        album = Album(title="Reissue", primary_artist_id=artist_id)

        album.update(original_release_id=original_album_id)

        assert album.original_release_id == original_album_id

    def test_update_self_reference_raises_error(self):
        """Should raise ValueError when setting original_release_id to self."""
        artist_id = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id)

        with pytest.raises(ValueError, match="Album cannot reference itself as original release"):
            album.update(original_release_id=album.id)

    def test_update_multiple_fields(self):
        """Should update multiple fields at once."""
        artist_id = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id)
        album.events.clear()

        album.update(
            release_type=ReleaseType.LIVE,
            original_release_year=2020,
            label="Test Records",
            description="A live album"
        )

        assert album.release_type == ReleaseType.LIVE
        assert album.original_release_year == 2020
        assert album.label == "Test Records"
        assert album.description == "A live album"
        assert len(album.events) == 1

    def test_update_emits_event(self):
        """Should emit AlbumUpdated event."""
        artist_id = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id)
        album.events.clear()

        album.update(title="New Title", label="New Label")

        assert len(album.events) == 1
        event = album.events[0]
        assert isinstance(event, AlbumUpdated)
        assert event.event_type == "album.updated"
        assert event.aggregate_id == album.id
        assert event.payload["title"] == "New Title"
        assert event.payload["label"] == "New Label"

    def test_update_updates_timestamp(self):
        """Should update the updated_at timestamp."""
        artist_id = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id)
        original_updated_at = album.updated_at

        album.update(title="New Title")

        assert album.updated_at > original_updated_at

    def test_update_cannot_change_id(self):
        """Should not change ID even if provided."""
        artist_id = uuid4()
        original_id = uuid4()
        album = Album(id=original_id, title="Album", primary_artist_id=artist_id)
        new_id = uuid4()

        album.update(id=new_id)

        assert album.id == original_id

    def test_update_cannot_change_created_at(self):
        """Should not change created_at timestamp."""
        artist_id = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id)
        original_created_at = album.created_at

        album.update(created_at=datetime(2020, 1, 1))

        assert album.created_at == original_created_at

    def test_update_cannot_modify_events_directly(self):
        """Should not modify events list through update."""
        artist_id = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id)
        original_events_count = len(album.events)

        album.update(events=[])

        # Should still have creation event + update event
        assert len(album.events) == original_events_count + 1


class TestAlbumEvents:
    """Test domain event handling."""

    def test_clear_events_returns_events(self):
        """Should return events when cleared."""
        artist_id = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id)

        events = album.clear_events()

        assert len(events) == 1
        assert isinstance(events[0], AlbumCreated)

    def test_clear_events_empties_list(self):
        """Should empty events list after clearing."""
        artist_id = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id)

        album.clear_events()

        assert album.events == []

    def test_multiple_updates_accumulate_events(self):
        """Should accumulate events from multiple updates."""
        artist_id = uuid4()
        album = Album(title="Album", primary_artist_id=artist_id)
        album.events.clear()

        album.update(title="Title 1")
        album.update(title="Title 2")
        album.update(title="Title 3")

        assert len(album.events) == 3
        for event in album.events:
            assert isinstance(event, AlbumUpdated)


class TestAlbumEdgeCases:
    """Test edge cases and special scenarios."""

    def test_unicode_title(self):
        """Should handle Unicode characters in title."""
        artist_id = uuid4()
        album = Album(title="Ænima", primary_artist_id=artist_id)

        assert album.title == "Ænima"

    def test_very_long_title(self):
        """Should handle very long titles."""
        artist_id = uuid4()
        long_title = "A" * 500
        album = Album(title=long_title, primary_artist_id=artist_id)

        assert album.title == long_title
        assert len(album.title) == 500

    def test_special_characters_in_title(self):
        """Should handle special characters in title."""
        artist_id = uuid4()
        album = Album(title="(What's the Story) Morning Glory?", primary_artist_id=artist_id)

        assert album.title == "(What's the Story) Morning Glory?"

    def test_release_date_and_year(self):
        """Should handle both release date and year."""
        artist_id = uuid4()
        release_date = date(1969, 9, 26)
        album = Album(
            title="Abbey Road",
            primary_artist_id=artist_id,
            original_release_year=1969,
            original_release_date=release_date,
        )

        assert album.original_release_year == 1969
        assert album.original_release_date == release_date

    def test_catalog_number_with_special_chars(self):
        """Should handle catalog numbers with special characters."""
        artist_id = uuid4()
        album = Album(
            title="Album",
            primary_artist_id=artist_id,
            catalog_number_base="CDPCSD-143",
        )

        assert album.catalog_number_base == "CDPCSD-143"

    def test_various_release_types(self):
        """Should handle all release type enum values."""
        artist_id = uuid4()

        for release_type in ReleaseType:
            album = Album(
                title=f"Album {release_type.value}",
                primary_artist_id=artist_id,
                release_type=release_type,
            )
            assert album.release_type == release_type
