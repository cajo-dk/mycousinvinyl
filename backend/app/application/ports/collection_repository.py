"""Collection repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID

from app.domain.entities import CollectionItem


class CollectionRepository(ABC):
    """
    Repository interface for CollectionItem entities.

    CRITICAL: All queries MUST filter by user_id for security.
    """

    @abstractmethod
    async def add(self, item: CollectionItem) -> CollectionItem:
        """Add a new item to collection."""
        pass

    @abstractmethod
    async def get(self, item_id: UUID, user_id: UUID) -> Optional[CollectionItem]:
        """
        Get collection item by ID.

        CRITICAL: Must verify user_id ownership.
        """
        pass

    @abstractmethod
    async def get_all_for_user(
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
            - media_condition: List[Condition] - Filter by media condition
            - sleeve_condition: List[Condition] - Filter by sleeve condition
            - rating_min: int - Minimum user rating
            - rating_max: int - Maximum user rating
            - price_min: Decimal - Minimum purchase price
            - price_max: Decimal - Maximum purchase price
            - tags: List[str] - Filter by tags (OR)

        Sort options:
            - date_added_desc, date_added_asc
            - rating_desc, rating_asc
            - price_desc, price_asc
            - condition_desc, condition_asc

        Returns:
            Tuple of (items list, total count)
        """
        pass

    @abstractmethod
    async def search_user_collection(
        self,
        user_id: UUID,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[CollectionItem], int]:
        """Search within user's collection (searches album/artist names)."""
        pass

    @abstractmethod
    async def update(self, item: CollectionItem, user_id: UUID) -> CollectionItem:
        """
        Update collection item.

        CRITICAL: Must verify user_id ownership.
        """
        pass

    @abstractmethod
    async def delete(self, item_id: UUID, user_id: UUID) -> None:
        """
        Delete collection item.

        CRITICAL: Must verify user_id ownership.
        """
        pass

    @abstractmethod
    async def exists(self, item_id: UUID, user_id: UUID) -> bool:
        """
        Check if collection item exists for user.

        CRITICAL: Must verify user_id ownership.
        """
        pass

    @abstractmethod
    async def get_all_with_details(
        self,
        user_id: UUID,
        query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "artist_album"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get collection items with joined artist and album details.

        Sort options:
            - artist_album (default)
            - date_added_desc, date_added_asc
        """
        pass

    @abstractmethod
    async def get_statistics(self, user_id: UUID) -> Dict[str, Any]:
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
        pass

    @abstractmethod
    async def get_owners_for_pressing(
        self,
        pressing_id: UUID,
        viewer_user_id: UUID,
        followed_user_ids: List[UUID]
    ) -> List[Tuple[UUID, int]]:
        """
        Get owners of a specific pressing (viewer + followed users with sharing enabled).

        Only returns users who:
        1. Own the pressing (have collection_items for this pressing_id)
        2. Have collection sharing enabled (for followed users)
        3. Are either the viewer themselves OR are in the followed_user_ids list

        Args:
            pressing_id: The pressing to check ownership for
            viewer_user_id: The current user viewing (always included if they own it)
            followed_user_ids: List of user IDs that viewer follows

        Returns:
            List of tuples (user_id, copy_count) where copy_count is the number
            of copies owned by that user
        """
        pass

    @abstractmethod
    async def exists_for_user_pressing(self, user_id: UUID, pressing_id: UUID) -> bool:
        """
        Check if user already has a pressing in their collection.

        CRITICAL: Must verify user_id ownership.
        """
        pass

    @abstractmethod
    async def get_owners_for_pressings(
        self,
        pressing_ids: List[UUID],
        viewer_user_id: UUID,
        followed_user_ids: List[UUID]
    ) -> Dict[UUID, List[Tuple[UUID, int]]]:
        """
        Get owners for multiple pressings (viewer + followed users with sharing enabled).

        Args:
            pressing_ids: Pressings to check ownership for
            viewer_user_id: The current user viewing (always included if they own it)
            followed_user_ids: List of user IDs that viewer follows

        Returns:
            Dictionary mapping pressing_id to list of (user_id, copy_count) tuples
        """
        pass

    @abstractmethod
    async def get_owners_for_album(
        self,
        album_id: UUID,
        viewer_user_id: UUID,
        followed_user_ids: List[UUID]
    ) -> List[Tuple[UUID, int]]:
        """
        Get owners of a specific album (any pressing) (viewer + followed users with sharing enabled).

        Only returns users who:
        1. Own at least one pressing of this album
        2. Have collection sharing enabled (for followed users)
        3. Are either the viewer themselves OR are in the followed_user_ids list

        Args:
            album_id: The album to check ownership for (any pressing)
            viewer_user_id: The current user viewing (always included if they own it)
            followed_user_ids: List of user IDs that viewer follows

        Returns:
            List of tuples (user_id, copy_count) where copy_count is the total
            number of pressings of this album owned by that user
        """
        pass

    @abstractmethod
    async def get_owners_for_albums(
        self,
        album_ids: List[UUID],
        viewer_user_id: UUID,
        followed_user_ids: List[UUID]
    ) -> Dict[UUID, List[Tuple[UUID, int]]]:
        """
        Get owners for multiple albums (viewer + followed users with sharing enabled).

        Args:
            album_ids: Albums to check ownership for (any pressing)
            viewer_user_id: The current user viewing (always included if they own it)
            followed_user_ids: List of user IDs that viewer follows

        Returns:
            Dictionary mapping album_id to list of (user_id, copy_count) tuples
        """
        pass
