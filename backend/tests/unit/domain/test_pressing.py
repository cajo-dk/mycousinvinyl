"""
Unit tests for Pressing domain entity.

Tests business rules and validation logic for the Pressing entity.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime

from app.domain.entities import Pressing
from app.domain.value_objects import (
    VinylFormat,
    VinylSpeed,
    VinylSize,
    EditionType,
    DataSource,
    VerificationStatus,
)


class TestPressingCreation:
    """Test pressing creation and validation."""

    def test_create_pressing_with_valid_data(self):
        """Should create pressing with valid data."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            pressing_country="USA",
            pressing_year=1969,
        )

        assert pressing.album_id == album_id
        assert pressing.format == VinylFormat.LP
        assert pressing.speed_rpm == VinylSpeed.RPM_33
        assert pressing.size_inches == VinylSize.SIZE_12
        assert pressing.pressing_country == "USA"
        assert pressing.pressing_year == 1969
        assert isinstance(pressing.id, UUID)
        assert pressing.disc_count == 1  # default
        assert pressing.data_source == DataSource.USER
        assert pressing.verification_status == VerificationStatus.UNVERIFIED

    def test_create_pressing_with_minimal_data(self):
        """Should create pressing with only required fields."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
        )

        assert pressing.album_id == album_id
        assert pressing.format == VinylFormat.LP
        assert pressing.speed_rpm == VinylSpeed.RPM_33
        assert pressing.size_inches == VinylSize.SIZE_12
        assert pressing.disc_count == 1

    def test_missing_album_id_raises_error(self):
        """Should raise ValueError when album_id is missing."""
        with pytest.raises(ValueError, match="Pressing must belong to an album"):
            Pressing(
                format=VinylFormat.LP,
                speed_rpm=VinylSpeed.RPM_33,
                size_inches=VinylSize.SIZE_12,
            )

    def test_none_album_id_raises_error(self):
        """Should raise ValueError when album_id is None."""
        with pytest.raises(ValueError, match="Pressing must belong to an album"):
            Pressing(
                album_id=None,
                format=VinylFormat.LP,
                speed_rpm=VinylSpeed.RPM_33,
                size_inches=VinylSize.SIZE_12,
            )

    def test_missing_format_raises_error(self):
        """Should raise ValueError when format is missing."""
        album_id = uuid4()
        with pytest.raises(ValueError, match="Vinyl format is required"):
            Pressing(
                album_id=album_id,
                speed_rpm=VinylSpeed.RPM_33,
                size_inches=VinylSize.SIZE_12,
            )

    def test_missing_speed_raises_error(self):
        """Should raise ValueError when speed is missing."""
        album_id = uuid4()
        with pytest.raises(ValueError, match="Playback speed is required"):
            Pressing(
                album_id=album_id,
                format=VinylFormat.LP,
                size_inches=VinylSize.SIZE_12,
            )

    def test_missing_size_raises_error(self):
        """Should raise ValueError when size is missing."""
        album_id = uuid4()
        with pytest.raises(ValueError, match="Vinyl size is required"):
            Pressing(
                album_id=album_id,
                format=VinylFormat.LP,
                speed_rpm=VinylSpeed.RPM_33,
            )

    def test_negative_disc_count_raises_error(self):
        """Should raise ValueError for negative disc count."""
        album_id = uuid4()
        with pytest.raises(ValueError, match="Disc count must be at least 1"):
            Pressing(
                album_id=album_id,
                format=VinylFormat.LP,
                speed_rpm=VinylSpeed.RPM_33,
                size_inches=VinylSize.SIZE_12,
                disc_count=-1,
            )

    def test_zero_disc_count_raises_error(self):
        """Should raise ValueError for zero disc count."""
        album_id = uuid4()
        with pytest.raises(ValueError, match="Disc count must be at least 1"):
            Pressing(
                album_id=album_id,
                format=VinylFormat.LP,
                speed_rpm=VinylSpeed.RPM_33,
                size_inches=VinylSize.SIZE_12,
                disc_count=0,
            )

    def test_multi_disc_pressing(self):
        """Should handle multi-disc pressings."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            disc_count=3,
        )

        assert pressing.disc_count == 3

    def test_custom_id_is_preserved(self):
        """Should preserve custom UUID if provided."""
        album_id = uuid4()
        custom_id = uuid4()
        pressing = Pressing(
            id=custom_id,
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
        )

        assert pressing.id == custom_id


class TestPressingFormats:
    """Test various vinyl formats."""

    def test_standard_lp(self):
        """Should create standard LP pressing."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
        )

        assert pressing.format == VinylFormat.LP
        assert pressing.speed_rpm == VinylSpeed.RPM_33
        assert pressing.size_inches == VinylSize.SIZE_12

    def test_45rpm_single(self):
        """Should create 45 RPM single."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.SINGLE,
            speed_rpm=VinylSpeed.RPM_45,
            size_inches=VinylSize.SIZE_7,
        )

        assert pressing.format == VinylFormat.SINGLE
        assert pressing.speed_rpm == VinylSpeed.RPM_45
        assert pressing.size_inches == VinylSize.SIZE_7

    def test_78rpm_shellac(self):
        """Should create 78 RPM shellac record."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_78,
            size_inches=VinylSize.SIZE_10,
        )

        assert pressing.speed_rpm == VinylSpeed.RPM_78

    def test_ep_format(self):
        """Should create EP format."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.EP,
            speed_rpm=VinylSpeed.RPM_45,
            size_inches=VinylSize.SIZE_7,
        )

        assert pressing.format == VinylFormat.EP

    def test_various_sizes(self):
        """Should handle all vinyl sizes."""
        album_id = uuid4()

        for size in VinylSize:
            pressing = Pressing(
                album_id=album_id,
                format=VinylFormat.LP,
                speed_rpm=VinylSpeed.RPM_33,
                size_inches=size,
            )
            assert pressing.size_inches == size


class TestPressingMetadata:
    """Test pressing metadata and optional fields."""

    def test_pressing_plant_info(self):
        """Should store pressing plant information."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            pressing_plant="Optimal Media",
            mastering_engineer="Bernie Grundman",
            mastering_studio="Bernie Grundman Mastering",
        )

        assert pressing.pressing_plant == "Optimal Media"
        assert pressing.mastering_engineer == "Bernie Grundman"
        assert pressing.mastering_studio == "Bernie Grundman Mastering"

    def test_vinyl_color(self):
        """Should store vinyl color information."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            vinyl_color="Transparent Red",
        )

        assert pressing.vinyl_color == "Transparent Red"

    def test_edition_types(self):
        """Should handle various edition types."""
        album_id = uuid4()

        for edition in EditionType:
            pressing = Pressing(
                album_id=album_id,
                format=VinylFormat.LP,
                speed_rpm=VinylSpeed.RPM_33,
                size_inches=VinylSize.SIZE_12,
                edition_type=edition,
            )
            assert pressing.edition_type == edition

    def test_limited_edition(self):
        """Should create limited edition pressing."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            edition_type=EditionType.LIMITED,
            notes="Limited to 500 copies on red vinyl",
        )

        assert pressing.edition_type == EditionType.LIMITED
        assert "Limited to 500 copies" in pressing.notes

    def test_barcode(self):
        """Should store barcode information."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            barcode="0724384260910",
        )

        assert pressing.barcode == "0724384260910"

    def test_label_design(self):
        """Should store label design information."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            label_design="Black label with silver text",
        )

        assert pressing.label_design == "Black label with silver text"

    def test_discogs_integration_fields(self):
        """Should store Discogs integration fields."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            discogs_release_id=123456,
            discogs_master_id=789012,
            master_title="Abbey Road",
        )

        assert pressing.discogs_release_id == 123456
        assert pressing.discogs_master_id == 789012
        assert pressing.master_title == "Abbey Road"


class TestPressingEvents:
    """Test domain event handling."""

    def test_clear_events_returns_events(self):
        """Should return events when cleared."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
        )
        pressing.events.append("test_event")

        events = pressing.clear_events()

        assert events == ["test_event"]

    def test_clear_events_empties_list(self):
        """Should empty events list after clearing."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
        )
        pressing.events.append("test_event")

        pressing.clear_events()

        assert pressing.events == []

    def test_events_list_starts_empty(self):
        """Should start with empty events list."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
        )

        assert pressing.events == []


class TestPressingEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_old_pressing(self):
        """Should handle very old pressings."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_78,
            size_inches=VinylSize.SIZE_10,
            pressing_year=1920,
        )

        assert pressing.pressing_year == 1920

    def test_recent_pressing(self):
        """Should handle recent pressings."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            pressing_year=2024,
        )

        assert pressing.pressing_year == 2024

    def test_boxset_multi_disc(self):
        """Should handle box set with many discs."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            disc_count=10,
            notes="Box set with 10 LPs",
        )

        assert pressing.disc_count == 10

    def test_created_by_tracking(self):
        """Should track who created the pressing."""
        album_id = uuid4()
        user_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
            created_by=user_id,
        )

        assert pressing.created_by == user_id

    def test_timestamps(self):
        """Should have creation and update timestamps."""
        album_id = uuid4()
        pressing = Pressing(
            album_id=album_id,
            format=VinylFormat.LP,
            speed_rpm=VinylSpeed.RPM_33,
            size_inches=VinylSize.SIZE_12,
        )

        assert isinstance(pressing.created_at, datetime)
        assert isinstance(pressing.updated_at, datetime)
        # Timestamps should be very close (within 1 second)
        assert abs((pressing.updated_at - pressing.created_at).total_seconds()) < 1
