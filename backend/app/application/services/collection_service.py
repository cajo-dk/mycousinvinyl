"""
Collection application service.

Orchestrates user collection management business operations.
Security-agnostic - authorization enforced at HTTP entrypoint layer.

IMPORTANT: All operations are user-scoped. The user_id parameter
must be provided from the authenticated context at the HTTP layer.
"""

from uuid import UUID
from typing import Optional, List, Tuple, Dict, Any
from decimal import Decimal
from datetime import date

from app.domain.entities import CollectionItem
from app.domain.events import ActivityEvent
from app.domain.value_objects import Condition
from app.application.ports.unit_of_work import UnitOfWork
from app.config import get_settings


class CollectionService:
    """
    Service for collection management operations.

    All methods require user_id for proper scoping.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.activity_topic = get_settings().activity_topic

    async def _get_preferred_currency(self, user_id: UUID) -> str:
        prefs = await self.uow.preferences_repository.get(user_id)
        return prefs.currency if prefs else "DKK"

    async def add_to_collection(
        self,
        user_id: UUID,
        pressing_id: UUID,
        media_condition: Condition,
        sleeve_condition: Condition,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        purchase_price: Optional[Decimal] = None,
        purchase_currency: Optional[str] = None,
        purchase_date: Optional[date] = None,
        seller: Optional[str] = None,
        storage_location: Optional[str] = None,
        defect_notes: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> CollectionItem:
        """
        Add a pressing to user's collection.

        Business rules enforced:
        - user_id and pressing_id are required
        - media_condition and sleeve_condition are required
        - Validates pressing exists
        """
        async with self.uow:
            # Validate pressing exists
            pressing_exists = await self.uow.pressing_repository.exists(pressing_id)
            if not pressing_exists:
                raise ValueError(f"Pressing {pressing_id} does not exist")

            preferred_currency = None
            if purchase_price is not None or purchase_currency is not None:
                preferred_currency = await self._get_preferred_currency(user_id)

            # Create domain entity (business rules enforced)
            item = CollectionItem(
                user_id=user_id,
                pressing_id=pressing_id,
                media_condition=media_condition,
                sleeve_condition=sleeve_condition,
                purchase_price=purchase_price,
                purchase_currency=preferred_currency,
                purchase_date=purchase_date,
                seller=seller,
                storage_location=storage_location,
                defect_notes=defect_notes,
                user_notes=notes,
            )

            # Persist within transaction
            result = await self.uow.collection_repository.add(item)

            pressing = await self.uow.pressing_repository.get(pressing_id)
            album_title = None
            album_id = None
            if pressing:
                album_id = pressing.album_id
                album = await self.uow.album_repository.get(pressing.album_id)
                album_title = album.title if album else None
            summary = album_title or str(result.id)
            ownership_event = ActivityEvent(
                operation="created",
                entity_type="pressing_ownership",
                entity_id=pressing_id,
                pressing_id=pressing_id,
                album_id=album_id,
                summary=summary,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=ownership_event,
                aggregate_id=pressing_id,
                aggregate_type='PressingOwnership',
                destination=self.activity_topic
            )
            await self.uow.commit()

        return result

    async def get_collection_item(
        self,
        item_id: UUID,
        user_id: UUID
    ) -> Optional[CollectionItem]:
        """
        Get a collection item by ID.

        SECURITY: Verifies user owns the item.
        """
        async with self.uow:
            return await self.uow.collection_repository.get(item_id, user_id)

    async def get_user_collection(
        self,
        user_id: UUID,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "date_added_desc",
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[CollectionItem], int]:
        """
        Get all collection items for a user with filters and sorting.

        Filters:
            - media_condition: List[Condition]
            - sleeve_condition: List[Condition]
            - rating_min: int
            - rating_max: int
            - price_min: Decimal
            - price_max: Decimal
            - tags: List[str]
        """
        async with self.uow:
            return await self.uow.collection_repository.get_all_for_user(
                user_id, filters, sort_by, limit, offset
            )

    async def search_collection(
        self,
        user_id: UUID,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[CollectionItem], int]:
        """
        Search within user's collection.

        Searches album titles and artist names.
        """
        async with self.uow:
            return await self.uow.collection_repository.search_user_collection(
                user_id, query, limit, offset
            )

    async def update_collection_item(
        self,
        item_id: UUID,
        user_id: UUID,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        **updates
    ) -> Optional[CollectionItem]:
        """
        Update a collection item.

        SECURITY: Verifies user owns the item.
        """
        async with self.uow:
            item = await self.uow.collection_repository.get(item_id, user_id)
            if not item:
                return None

            if "purchase_price" in updates or "purchase_currency" in updates:
                if updates.get("purchase_price") is not None or updates.get("purchase_currency") is not None:
                    updates["purchase_currency"] = await self._get_preferred_currency(user_id)

            # Apply updates to domain entity
            for key, value in updates.items():
                if hasattr(item, key) and key not in ['id', 'user_id', 'created_at']:
                    setattr(item, key, value)

            result = await self.uow.collection_repository.update(item, user_id)

            album_title = None
            pressing = await self.uow.pressing_repository.get(item.pressing_id)
            if pressing:
                album = await self.uow.album_repository.get(pressing.album_id)
                album_title = album.title if album else None
            summary = album_title or str(result.id)
            activity_event = ActivityEvent(
                operation="updated",
                entity_type="collection_item",
                entity_id=result.id,
                pressing_id=item.pressing_id,
                summary=summary,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=activity_event,
                aggregate_id=result.id,
                aggregate_type='CollectionItem',
                destination=self.activity_topic
            )
            await self.uow.commit()

        return result

    async def update_condition(
        self,
        item_id: UUID,
        user_id: UUID,
        media_condition: Optional[Condition] = None,
        sleeve_condition: Optional[Condition] = None,
        defect_notes: Optional[str] = None
    ) -> Optional[CollectionItem]:
        """
        Update condition information for a collection item.

        Uses domain entity business method.
        """
        async with self.uow:
            item = await self.uow.collection_repository.get(item_id, user_id)
            if not item:
                return None

            # Use domain entity business method
            item.update_condition(media_condition, sleeve_condition, defect_notes)

            result = await self.uow.collection_repository.update(item, user_id)
            await self.uow.commit()

        return result

    async def increment_album_play_count(
        self,
        album_id: UUID,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """
        Increment per-user album play count.
        """
        async with self.uow:
            has_album = await self.uow.collection_repository.user_has_album(user_id, album_id)
            if not has_album:
                raise ValueError("Album not found in user's collection")

            result = await self.uow.collection_repository.increment_album_play_count(
                user_id=user_id,
                album_id=album_id,
            )
            await self.uow.commit()
            return result

    async def get_played_albums_ytd(
        self,
        user_id: UUID,
        year: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get played albums for a user in a given year.
        """
        async with self.uow:
            return await self.uow.collection_repository.get_played_albums_ytd(
                user_id=user_id,
                year=year,
                limit=limit,
                offset=offset
            )

    async def update_purchase_info(
        self,
        item_id: UUID,
        user_id: UUID,
        price: Optional[Decimal] = None,
        currency: Optional[str] = None,
        purchase_date: Optional[date] = None,
        seller: Optional[str] = None
    ) -> Optional[CollectionItem]:
        """
        Update purchase information for a collection item.

        Uses domain entity business method with validation.
        """
        async with self.uow:
            item = await self.uow.collection_repository.get(item_id, user_id)
            if not item:
                return None

            preferred_currency = currency
            if price is not None or currency is not None:
                preferred_currency = await self._get_preferred_currency(user_id)

            # Use domain entity business method (validates price >= 0)
            item.update_purchase_info(price, preferred_currency, purchase_date, seller)

            result = await self.uow.collection_repository.update(item, user_id)
            await self.uow.commit()

        return result

    async def update_rating(
        self,
        item_id: UUID,
        user_id: UUID,
        rating: int,
        notes: Optional[str] = None
    ) -> Optional[CollectionItem]:
        """
        Update user rating and notes for a collection item.

        Uses domain entity business method with validation (0-5).
        """
        async with self.uow:
            item = await self.uow.collection_repository.get(item_id, user_id)
            if not item:
                return None

            # Use domain entity business method (validates 0-5 range)
            item.update_rating(rating, notes)

            result = await self.uow.collection_repository.update(item, user_id)
            await self.uow.commit()

        return result

    async def increment_play_count(
        self,
        item_id: UUID,
        user_id: UUID
    ) -> Optional[CollectionItem]:
        """
        Increment play count and update last played date.

        Uses domain entity business method.
        """
        async with self.uow:
            item = await self.uow.collection_repository.get(item_id, user_id)
            if not item:
                return None

            # Use domain entity business method
            item.increment_play_count()

            result = await self.uow.collection_repository.update(item, user_id)
            await self.uow.commit()

        return result

    async def remove_from_collection(
        self,
        item_id: UUID,
        user_id: UUID,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> bool:
        """
        Remove a pressing from user's collection.

        SECURITY: Verifies user owns the item.
        """
        async with self.uow:
            item = await self.uow.collection_repository.get(item_id, user_id)
            if not item:
                return False

            album_title = None
            album_id = None
            pressing = await self.uow.pressing_repository.get(item.pressing_id)
            if pressing:
                album_id = pressing.album_id
                album = await self.uow.album_repository.get(pressing.album_id)
                album_title = album.title if album else None
            summary = album_title or str(item.id)

            await self.uow.collection_repository.delete(item_id, user_id)

            ownership_event = ActivityEvent(
                operation="deleted",
                entity_type="pressing_ownership",
                entity_id=item.pressing_id,
                pressing_id=item.pressing_id,
                album_id=album_id,
                summary=summary,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email
            )
            await self.uow.outbox_repository.add_event(
                event=ownership_event,
                aggregate_id=item.pressing_id,
                aggregate_type='PressingOwnership',
                destination=self.activity_topic
            )
            await self.uow.commit()

        return True

    async def get_collection_with_details(
        self,
        user_id: UUID,
        query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "artist_album"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get collection items with joined artist and album details.

        Returns enriched data for hierarchical display in UI.
        """
        async with self.uow:
            return await self.uow.collection_repository.get_all_with_details(
                user_id, query, limit, offset, sort_by
            )

    async def get_collection_statistics(
        self,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get collection statistics for user.

        Returns:
            {
                "total_albums": int,
                "total_purchase_price": Decimal,
                "min_value": Decimal,
                "avg_value": Decimal,
                "max_value": Decimal,
                "currency": str
            }
        """
        async with self.uow:
            stats = await self.uow.collection_repository.get_statistics(user_id)
            stats["top_artists"] = await self.uow.collection_repository.get_top_artists_global()
            stats["top_albums"] = await self.uow.collection_repository.get_top_albums_global()
            stats["currency"] = await self._get_preferred_currency(user_id)
            return stats
