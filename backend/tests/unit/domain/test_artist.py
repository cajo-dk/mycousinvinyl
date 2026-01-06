"""
Unit tests for Artist domain entity.

Tests business rules and validation logic for the Artist entity.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime

from app.domain.entities import Artist
from app.domain.value_objects import ArtistType, DataSource, VerificationStatus


class TestArtistCreation:
    """Test artist creation and validation."""

    def test_create_artist_with_valid_data(self):
        """Should create artist with valid data."""
        artist = Artist(
            name="The Beatles",
            type=ArtistType.GROUP,
            country="GBR",
        )

        assert artist.name == "The Beatles"
        assert artist.type == ArtistType.GROUP
        assert artist.country == "GBR"
        assert isinstance(artist.id, UUID)
        assert isinstance(artist.created_at, datetime)
        assert artist.data_source == DataSource.USER
        assert artist.verification_status == VerificationStatus.UNVERIFIED

    def test_create_artist_with_minimal_data(self):
        """Should create artist with only required name field."""
        artist = Artist(name="Miles Davis")

        assert artist.name == "Miles Davis"
        assert artist.type == ArtistType.PERSON  # default
        assert artist.country is None
        assert artist.aliases == []
        assert artist.notes is None

    def test_name_is_stripped(self):
        """Should strip whitespace from artist name."""
        artist = Artist(name="  Pink Floyd  ")

        assert artist.name == "Pink Floyd"

    def test_empty_name_raises_error(self):
        """Should raise ValueError for empty name."""
        with pytest.raises(ValueError, match="Artist name is required"):
            Artist(name="")

    def test_whitespace_only_name_raises_error(self):
        """Should raise ValueError for whitespace-only name."""
        with pytest.raises(ValueError, match="Artist name is required"):
            Artist(name="   ")

    def test_missing_name_raises_error(self):
        """Should raise ValueError when name is not provided."""
        with pytest.raises(ValueError, match="Artist name is required"):
            Artist()

    def test_custom_id_is_preserved(self):
        """Should preserve custom UUID if provided."""
        custom_id = uuid4()
        artist = Artist(id=custom_id, name="Bob Dylan")

        assert artist.id == custom_id

    def test_created_by_is_set(self):
        """Should set created_by if provided."""
        user_id = uuid4()
        artist = Artist(name="Nina Simone", created_by=user_id)

        assert artist.created_by == user_id


class TestArtistSortName:
    """Test sort name generation logic."""

    def test_sort_name_auto_generated_for_article_the(self):
        """Should move 'The' to end for sort name."""
        artist = Artist(name="The Beatles")

        assert artist.name == "The Beatles"
        assert artist.sort_name == "Beatles, The"

    def test_sort_name_auto_generated_for_article_a(self):
        """Should move 'A' to end for sort name."""
        artist = Artist(name="A Tribe Called Quest")

        assert artist.sort_name == "Tribe Called Quest, A"

    def test_sort_name_auto_generated_for_article_an(self):
        """Should move 'An' to end for sort name."""
        artist = Artist(name="An Early Bird")

        assert artist.sort_name == "Early Bird, An"

    def test_sort_name_unchanged_when_no_article(self):
        """Should keep sort name same as name when no article."""
        artist = Artist(name="Miles Davis")

        assert artist.sort_name == "Miles Davis"

    def test_sort_name_case_sensitive(self):
        """Should only move article if properly capitalized."""
        artist = Artist(name="the beatles")

        # Should NOT move 'the' because it's lowercase
        assert artist.sort_name == "the beatles"

    def test_custom_sort_name_preserved(self):
        """Should preserve custom sort name if provided."""
        artist = Artist(name="The Beatles", sort_name="Beatles")

        assert artist.sort_name == "Beatles"

    def test_article_in_middle_not_moved(self):
        """Should not move article if not at start."""
        artist = Artist(name="Echo and the Bunnymen")

        assert artist.sort_name == "Echo and the Bunnymen"


class TestArtistUpdate:
    """Test artist update method."""

    def test_update_name(self):
        """Should update artist name and regenerate sort name."""
        artist = Artist(name="The Beatles")
        original_updated_at = artist.updated_at

        artist.update(name="Beatles")

        assert artist.name == "Beatles"
        assert artist.sort_name == "Beatles"
        assert artist.updated_at > original_updated_at

    def test_update_name_with_article(self):
        """Should update name and auto-generate new sort name."""
        artist = Artist(name="Pink Floyd")

        artist.update(name="The Pink Floyd")

        assert artist.name == "The Pink Floyd"
        assert artist.sort_name == "Pink Floyd, The"

    def test_update_type(self):
        """Should update artist type."""
        artist = Artist(name="Miles Davis", type=ArtistType.PERSON)

        artist.update(type=ArtistType.GROUP)

        assert artist.type == ArtistType.GROUP

    def test_update_country(self):
        """Should update country."""
        artist = Artist(name="The Beatles")

        artist.update(country="GBR")

        assert artist.country == "GBR"

    def test_update_multiple_fields(self):
        """Should update multiple fields at once."""
        artist = Artist(name="Bob Dylan")

        artist.update(
            type=ArtistType.PERSON,
            country="USA",
            active_years="1959-present",
            notes="American singer-songwriter"
        )

        assert artist.type == ArtistType.PERSON
        assert artist.country == "USA"
        assert artist.active_years == "1959-present"
        assert artist.notes == "American singer-songwriter"

    def test_update_empty_name_raises_error(self):
        """Should raise ValueError when updating to empty name."""
        artist = Artist(name="The Beatles")

        with pytest.raises(ValueError, match="Artist name cannot be empty"):
            artist.update(name="")

    def test_update_whitespace_name_raises_error(self):
        """Should raise ValueError when updating to whitespace name."""
        artist = Artist(name="The Beatles")

        with pytest.raises(ValueError, match="Artist name cannot be empty"):
            artist.update(name="   ")

    def test_update_strips_whitespace(self):
        """Should strip whitespace from updated name."""
        artist = Artist(name="The Beatles")

        artist.update(name="  Beatles  ")

        assert artist.name == "Beatles"

    def test_update_cannot_change_id(self):
        """Should not change ID even if provided."""
        original_id = uuid4()
        artist = Artist(id=original_id, name="The Beatles")
        new_id = uuid4()

        artist.update(id=new_id)

        assert artist.id == original_id

    def test_update_cannot_change_created_at(self):
        """Should not change created_at timestamp."""
        artist = Artist(name="The Beatles")
        original_created_at = artist.created_at
        new_time = datetime(2020, 1, 1)

        artist.update(created_at=new_time)

        assert artist.created_at == original_created_at

    def test_update_cannot_change_created_by(self):
        """Should not change created_by even if provided."""
        user_id = uuid4()
        artist = Artist(name="The Beatles", created_by=user_id)
        new_user_id = uuid4()

        artist.update(created_by=new_user_id)

        assert artist.created_by == user_id

    def test_update_with_no_args_updates_timestamp(self):
        """Should update timestamp even with no field changes."""
        artist = Artist(name="The Beatles")
        original_updated_at = artist.updated_at

        artist.update()

        assert artist.updated_at > original_updated_at


class TestArtistEvents:
    """Test domain event handling."""

    def test_clear_events_returns_events(self):
        """Should return events when cleared."""
        artist = Artist(name="The Beatles")
        artist.events.append("test_event")

        events = artist.clear_events()

        assert events == ["test_event"]

    def test_clear_events_empties_list(self):
        """Should empty events list after clearing."""
        artist = Artist(name="The Beatles")
        artist.events.append("test_event")

        artist.clear_events()

        assert artist.events == []

    def test_events_list_starts_empty(self):
        """Should start with empty events list."""
        artist = Artist(name="The Beatles")

        assert artist.events == []


class TestArtistEdgeCases:
    """Test edge cases and special scenarios."""

    def test_unicode_name(self):
        """Should handle Unicode characters in name."""
        artist = Artist(name="Björk")

        assert artist.name == "Björk"
        assert artist.sort_name == "Björk"

    def test_very_long_name(self):
        """Should handle very long names."""
        long_name = "A" * 500
        artist = Artist(name=long_name)

        assert artist.name == long_name
        assert len(artist.name) == 500

    def test_name_with_special_characters(self):
        """Should handle special characters in name."""
        artist = Artist(name="AC/DC")

        assert artist.name == "AC/DC"
        assert artist.sort_name == "AC/DC"

    def test_multiple_spaces_in_name(self):
        """Should preserve internal spaces in name."""
        artist = Artist(name="Crosby, Stills, Nash & Young")

        assert artist.name == "Crosby, Stills, Nash & Young"

    def test_aliases_list(self):
        """Should handle list of aliases."""
        artist = Artist(
            name="The Artist Formerly Known as Prince",
            aliases=["Prince", "TAFKAP", "Symbol"]
        )

        assert len(artist.aliases) == 3
        assert "Prince" in artist.aliases
