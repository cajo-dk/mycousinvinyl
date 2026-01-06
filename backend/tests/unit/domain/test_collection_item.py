"""
Unit tests for CollectionItem domain entity.

Tests business rules and validation logic for the CollectionItem entity.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, date
from decimal import Decimal

from app.domain.entities import CollectionItem, CollectionItemAdded, CollectionItemUpdated
from app.domain.value_objects import Condition


class TestCollectionItemCreation:
    """Test collection item creation and validation."""

    def test_create_collection_item_with_valid_data(self):
        """Should create collection item with valid data."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG_PLUS,
            sleeve_condition=Condition.VG,
            purchase_price=Decimal("25.99"),
            purchase_currency="DKK",
        )

        assert item.user_id == user_id
        assert item.pressing_id == pressing_id
        assert item.media_condition == Condition.VG_PLUS
        assert item.sleeve_condition == Condition.VG
        assert item.purchase_price == Decimal("25.99")
        assert item.purchase_currency == "DKK"
        assert isinstance(item.id, UUID)
        assert item.play_count == 0
        assert item.user_rating is None

    def test_create_with_minimal_data(self):
        """Should create item with only required fields."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.MINT,
            sleeve_condition=Condition.MINT,
        )

        assert item.user_id == user_id
        assert item.pressing_id == pressing_id
        assert item.media_condition == Condition.MINT
        assert item.sleeve_condition == Condition.MINT

    def test_missing_user_id_raises_error(self):
        """Should raise ValueError when user_id is missing."""
        pressing_id = uuid4()
        with pytest.raises(ValueError, match="Collection item must belong to a user"):
            CollectionItem(
                pressing_id=pressing_id,
                media_condition=Condition.VG,
                sleeve_condition=Condition.VG,
            )

    def test_none_user_id_raises_error(self):
        """Should raise ValueError when user_id is None."""
        pressing_id = uuid4()
        with pytest.raises(ValueError, match="Collection item must belong to a user"):
            CollectionItem(
                user_id=None,
                pressing_id=pressing_id,
                media_condition=Condition.VG,
                sleeve_condition=Condition.VG,
            )

    def test_missing_pressing_id_raises_error(self):
        """Should raise ValueError when pressing_id is missing."""
        user_id = uuid4()
        with pytest.raises(ValueError, match="Collection item must reference a pressing"):
            CollectionItem(
                user_id=user_id,
                media_condition=Condition.VG,
                sleeve_condition=Condition.VG,
            )

    def test_missing_media_condition_raises_error(self):
        """Should raise ValueError when media_condition is missing."""
        user_id = uuid4()
        pressing_id = uuid4()
        with pytest.raises(ValueError, match="Media condition is required"):
            CollectionItem(
                user_id=user_id,
                pressing_id=pressing_id,
                sleeve_condition=Condition.VG,
            )

    def test_missing_sleeve_condition_raises_error(self):
        """Should raise ValueError when sleeve_condition is missing."""
        user_id = uuid4()
        pressing_id = uuid4()
        with pytest.raises(ValueError, match="Sleeve condition is required"):
            CollectionItem(
                user_id=user_id,
                pressing_id=pressing_id,
                media_condition=Condition.VG,
            )

    def test_negative_purchase_price_raises_error(self):
        """Should raise ValueError for negative purchase price."""
        user_id = uuid4()
        pressing_id = uuid4()
        with pytest.raises(ValueError, match="Purchase price cannot be negative"):
            CollectionItem(
                user_id=user_id,
                pressing_id=pressing_id,
                media_condition=Condition.VG,
                sleeve_condition=Condition.VG,
                purchase_price=Decimal("-10.00"),
            )

    def test_invalid_rating_negative_raises_error(self):
        """Should raise ValueError for negative rating."""
        user_id = uuid4()
        pressing_id = uuid4()
        with pytest.raises(ValueError, match="User rating must be between 0 and 5"):
            CollectionItem(
                user_id=user_id,
                pressing_id=pressing_id,
                media_condition=Condition.VG,
                sleeve_condition=Condition.VG,
                user_rating=-1,
            )

    def test_invalid_rating_too_high_raises_error(self):
        """Should raise ValueError for rating above 5."""
        user_id = uuid4()
        pressing_id = uuid4()
        with pytest.raises(ValueError, match="User rating must be between 0 and 5"):
            CollectionItem(
                user_id=user_id,
                pressing_id=pressing_id,
                media_condition=Condition.VG,
                sleeve_condition=Condition.VG,
                user_rating=6,
            )

    def test_zero_purchase_price_is_valid(self):
        """Should allow zero purchase price (free/gift)."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
            purchase_price=Decimal("0.00"),
        )

        assert item.purchase_price == Decimal("0.00")

    def test_creation_emits_event(self):
        """Should emit CollectionItemAdded event on creation."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.MINT,
            sleeve_condition=Condition.MINT,
        )

        assert len(item.events) == 1
        event = item.events[0]
        assert isinstance(event, CollectionItemAdded)
        assert event.event_type == "collection.item.added"
        assert event.aggregate_id == item.id


class TestConditionValues:
    """Test various condition values."""

    def test_all_mint(self):
        """Should handle mint condition."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.MINT,
            sleeve_condition=Condition.MINT,
        )

        assert item.media_condition == Condition.MINT
        assert item.sleeve_condition == Condition.MINT

    def test_different_conditions(self):
        """Should allow different media and sleeve conditions."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.NEAR_MINT,
            sleeve_condition=Condition.VG_PLUS,
        )

        assert item.media_condition == Condition.NEAR_MINT
        assert item.sleeve_condition == Condition.VG_PLUS

    def test_all_condition_values(self):
        """Should handle all condition enum values."""
        user_id = uuid4()
        pressing_id = uuid4()

        for condition in Condition:
            item = CollectionItem(
                user_id=user_id,
                pressing_id=pressing_id,
                media_condition=condition,
                sleeve_condition=condition,
            )
            assert item.media_condition == condition
            assert item.sleeve_condition == condition


class TestUpdateCondition:
    """Test update_condition method."""

    def test_update_media_condition(self):
        """Should update media condition."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.MINT,
            sleeve_condition=Condition.MINT,
        )
        item.events.clear()

        item.update_condition(media_condition=Condition.VG_PLUS)

        assert item.media_condition == Condition.VG_PLUS
        assert len(item.events) == 1
        assert isinstance(item.events[0], CollectionItemUpdated)

    def test_update_sleeve_condition(self):
        """Should update sleeve condition."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.MINT,
            sleeve_condition=Condition.MINT,
        )

        item.update_condition(sleeve_condition=Condition.GOOD)

        assert item.sleeve_condition == Condition.GOOD

    def test_update_both_conditions(self):
        """Should update both conditions at once."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.MINT,
            sleeve_condition=Condition.MINT,
        )

        item.update_condition(
            media_condition=Condition.VG,
            sleeve_condition=Condition.GOOD,
        )

        assert item.media_condition == Condition.VG
        assert item.sleeve_condition == Condition.GOOD

    def test_update_defect_notes(self):
        """Should update defect notes."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.update_condition(defect_notes="Small scratch on side B")

        assert item.defect_notes == "Small scratch on side B"

    def test_update_condition_updates_timestamp(self):
        """Should update the updated_at timestamp."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.MINT,
            sleeve_condition=Condition.MINT,
        )
        original_updated_at = item.updated_at

        item.update_condition(media_condition=Condition.VG)

        assert item.updated_at > original_updated_at


class TestUpdatePurchaseInfo:
    """Test update_purchase_info method."""

    def test_update_purchase_price(self):
        """Should update purchase price."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.update_purchase_info(price=Decimal("29.99"))

        assert item.purchase_price == Decimal("29.99")

    def test_update_purchase_currency(self):
        """Should update purchase currency."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.update_purchase_info(currency="EUR")

        assert item.purchase_currency == "EUR"

    def test_update_purchase_date(self):
        """Should update purchase date."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )
        purchase_date = date(2024, 1, 15)

        item.update_purchase_info(purchase_date=purchase_date)

        assert item.purchase_date == purchase_date

    def test_update_seller(self):
        """Should update seller information."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.update_purchase_info(seller="Discogs Seller XYZ")

        assert item.seller == "Discogs Seller XYZ"

    def test_update_all_purchase_info(self):
        """Should update all purchase information at once."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )
        purchase_date = date(2024, 1, 15)

        item.update_purchase_info(
            price=Decimal("45.50"),
            currency="GBP",
            purchase_date=purchase_date,
            seller="Record Shop",
        )

        assert item.purchase_price == Decimal("45.50")
        assert item.purchase_currency == "GBP"
        assert item.purchase_date == purchase_date
        assert item.seller == "Record Shop"

    def test_negative_price_raises_error(self):
        """Should raise ValueError for negative price."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        with pytest.raises(ValueError, match="Purchase price cannot be negative"):
            item.update_purchase_info(price=Decimal("-10.00"))

    def test_update_purchase_info_updates_timestamp(self):
        """Should update the updated_at timestamp."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )
        original_updated_at = item.updated_at

        item.update_purchase_info(price=Decimal("25.00"))

        assert item.updated_at > original_updated_at


class TestUpdateRating:
    """Test update_rating method."""

    def test_update_rating_valid(self):
        """Should update user rating."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )
        item.events.clear()

        item.update_rating(4)

        assert item.user_rating == 4
        assert len(item.events) == 1
        assert isinstance(item.events[0], CollectionItemUpdated)

    def test_update_rating_with_notes(self):
        """Should update rating and notes."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.update_rating(5, notes="Excellent pressing, no surface noise")

        assert item.user_rating == 5
        assert item.user_notes == "Excellent pressing, no surface noise"

    def test_update_rating_zero_is_valid(self):
        """Should allow zero rating."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.update_rating(0)

        assert item.user_rating == 0

    def test_update_rating_five_is_valid(self):
        """Should allow maximum rating of 5."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.update_rating(5)

        assert item.user_rating == 5

    def test_update_rating_negative_raises_error(self):
        """Should raise ValueError for negative rating."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        with pytest.raises(ValueError, match="User rating must be between 0 and 5"):
            item.update_rating(-1)

    def test_update_rating_too_high_raises_error(self):
        """Should raise ValueError for rating above 5."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        with pytest.raises(ValueError, match="User rating must be between 0 and 5"):
            item.update_rating(6)

    def test_update_rating_updates_timestamp(self):
        """Should update the updated_at timestamp."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )
        original_updated_at = item.updated_at

        item.update_rating(4)

        assert item.updated_at > original_updated_at


class TestIncrementPlayCount:
    """Test increment_play_count method."""

    def test_increment_from_zero(self):
        """Should increment play count from zero."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.increment_play_count()

        assert item.play_count == 1
        assert item.last_played_date == date.today()

    def test_increment_multiple_times(self):
        """Should increment play count multiple times."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.increment_play_count()
        item.increment_play_count()
        item.increment_play_count()

        assert item.play_count == 3

    def test_increment_updates_last_played(self):
        """Should update last_played_date to today."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.increment_play_count()

        assert item.last_played_date == date.today()

    def test_increment_updates_timestamp(self):
        """Should update the updated_at timestamp."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )
        original_updated_at = item.updated_at

        item.increment_play_count()

        assert item.updated_at > original_updated_at


class TestCollectionItemEvents:
    """Test domain event handling."""

    def test_clear_events_returns_events(self):
        """Should return events when cleared."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        events = item.clear_events()

        assert len(events) == 1
        assert isinstance(events[0], CollectionItemAdded)

    def test_clear_events_empties_list(self):
        """Should empty events list after clearing."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        item.clear_events()

        assert item.events == []


class TestCollectionItemEdgeCases:
    """Test edge cases and special scenarios."""

    def test_tags_list(self):
        """Should handle list of tags."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
            tags=["wishlist", "favorites", "jazz"],
        )

        assert len(item.tags) == 3
        assert "favorites" in item.tags

    def test_storage_location(self):
        """Should store location information."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
            storage_location="Shelf A, Position 12",
        )

        assert item.storage_location == "Shelf A, Position 12"

    def test_play_tested_flag(self):
        """Should track if item has been play tested."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
            play_tested=True,
        )

        assert item.play_tested is True

    def test_high_value_item(self):
        """Should handle expensive pressings."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.MINT,
            sleeve_condition=Condition.MINT,
            purchase_price=Decimal("5000.00"),
            purchase_currency="DKK",
        )

        assert item.purchase_price == Decimal("5000.00")

    def test_date_added_tracking(self):
        """Should track when item was added to collection."""
        user_id = uuid4()
        pressing_id = uuid4()
        item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing_id,
            media_condition=Condition.VG,
            sleeve_condition=Condition.VG,
        )

        assert isinstance(item.date_added, datetime)
        assert item.date_added <= datetime.utcnow()
