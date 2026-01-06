"""
Port interface for Discogs cache repository.
"""

from abc import ABC, abstractmethod
from typing import Optional


class DiscogsCacheRepository(ABC):
    """Abstract repository for caching Discogs API responses."""

    @abstractmethod
    async def get_page_cache(
        self, master_id: int, page: int, per_page: int
    ) -> Optional[dict]:
        """
        Get cached page data if not expired.

        Args:
            master_id: Discogs master ID
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Cached response dict if found and not expired, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def set_page_cache(
        self, master_id: int, page: int, per_page: int, data: dict
    ) -> None:
        """
        Cache page data with 24-hour TTL.

        Args:
            master_id: Discogs master ID
            page: Page number (1-indexed)
            per_page: Items per page
            data: Response data to cache
        """
        raise NotImplementedError

    @abstractmethod
    async def get_release_cache(self, release_id: int) -> Optional[dict]:
        """
        Get cached release data if not expired.

        Args:
            release_id: Discogs release ID

        Returns:
            Cached release data if found and not expired, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def set_release_cache(self, release_id: int, data: dict) -> None:
        """
        Cache release data with 7-day TTL.

        Args:
            release_id: Discogs release ID
            data: Release data to cache
        """
        raise NotImplementedError

    @abstractmethod
    async def get_search_cache(self, cache_key: str) -> Optional[dict]:
        """
        Get cached search results if not expired.

        Args:
            cache_key: Cache key for the search query

        Returns:
            Cached search results if found and not expired, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def set_search_cache(self, cache_key: str, data: dict) -> None:
        """
        Cache search results with 24-hour TTL.

        Args:
            cache_key: Cache key for the search query
            data: Search results to cache
        """
        raise NotImplementedError

    @abstractmethod
    async def invalidate_master(self, master_id: int) -> int:
        """
        Delete all cached pages for a master.

        Args:
            master_id: Discogs master ID

        Returns:
            Number of cache entries deleted
        """
        raise NotImplementedError

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """
        Delete expired cache entries from both tables.

        Returns:
            Number of cache entries deleted
        """
        raise NotImplementedError
