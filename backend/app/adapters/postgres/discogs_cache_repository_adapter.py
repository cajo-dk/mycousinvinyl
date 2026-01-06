"""
PostgreSQL adapter for Discogs cache repository.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.discogs_cache_repository import DiscogsCacheRepository

logger = logging.getLogger(__name__)


class PostgresDiscogsCacheRepository(DiscogsCacheRepository):
    """PostgreSQL implementation of Discogs cache repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _build_cache_key(self, master_id: int, page: int, per_page: int) -> str:
        """Build cache key for page cache."""
        return f"master_releases:{master_id}:page:{page}:per_page:{per_page}"

    async def get_page_cache(
        self, master_id: int, page: int, per_page: int
    ) -> Optional[dict]:
        """Get cached page data if not expired."""
        cache_key = self._build_cache_key(master_id, page, per_page)

        query = text("""
            SELECT response_data
            FROM discogs_cache_pages
            WHERE cache_key = :cache_key
              AND expires_at > NOW()
        """)

        result = await self._session.execute(
            query, {"cache_key": cache_key}
        )
        row = result.fetchone()

        if row:
            logger.info(f"Cache hit: {cache_key}")
            return row[0]  # JSONB column returns dict

        logger.info(f"Cache miss: {cache_key}")
        return None

    async def set_page_cache(
        self, master_id: int, page: int, per_page: int, data: dict
    ) -> None:
        """Cache page data with 24-hour TTL."""
        cache_key = self._build_cache_key(master_id, page, per_page)

        # Upsert: Insert or update if key exists
        query = text("""
            INSERT INTO discogs_cache_pages (
                cache_key, master_id, page, per_page, response_data, cached_at, expires_at
            )
            VALUES (
                :cache_key, :master_id, :page, :per_page, CAST(:response_data AS jsonb),
                NOW(), NOW() + INTERVAL '24 hours'
            )
            ON CONFLICT (cache_key) DO UPDATE SET
                response_data = EXCLUDED.response_data,
                cached_at = NOW(),
                expires_at = NOW() + INTERVAL '24 hours'
        """)

        await self._session.execute(
            query,
            {
                "cache_key": cache_key,
                "master_id": master_id,
                "page": page,
                "per_page": per_page,
                "response_data": json.dumps(data),
            },
        )
        await self._session.commit()

        logger.info(f"Cache set: {cache_key}")

    async def get_release_cache(self, release_id: int) -> Optional[dict]:
        """Get cached release data if not expired."""
        query = text("""
            SELECT release_data
            FROM discogs_cache_releases
            WHERE release_id = :release_id
              AND expires_at > NOW()
        """)

        result = await self._session.execute(
            query, {"release_id": release_id}
        )
        row = result.fetchone()

        if row:
            logger.debug(f"Release cache hit: {release_id}")
            return row[0]  # JSONB column returns dict

        logger.debug(f"Release cache miss: {release_id}")
        return None

    async def set_release_cache(self, release_id: int, data: dict) -> None:
        """Cache release data with 7-day TTL."""
        # Upsert: Insert or update if key exists
        query = text("""
            INSERT INTO discogs_cache_releases (
                release_id, release_data, cached_at, expires_at
            )
            VALUES (
                :release_id, CAST(:release_data AS jsonb),
                NOW(), NOW() + INTERVAL '7 days'
            )
            ON CONFLICT (release_id) DO UPDATE SET
                release_data = EXCLUDED.release_data,
                cached_at = NOW(),
                expires_at = NOW() + INTERVAL '7 days'
        """)

        await self._session.execute(
            query,
            {
                "release_id": release_id,
                "release_data": json.dumps(data),
            },
        )
        await self._session.commit()

        logger.debug(f"Release cache set: {release_id}")

    async def get_search_cache(self, cache_key: str) -> Optional[dict]:
        """Get cached search results if not expired."""
        query = text("""
            SELECT response_data
            FROM discogs_cache_pages
            WHERE cache_key = :cache_key
              AND expires_at > NOW()
        """)

        result = await self._session.execute(query, {"cache_key": cache_key})
        row = result.fetchone()

        if row:
            logger.info(f"Search cache hit: {cache_key}")
            return row[0]

        logger.info(f"Search cache miss: {cache_key}")
        return None

    async def set_search_cache(self, cache_key: str, data: dict) -> None:
        """Cache search results with 24-hour TTL."""
        # Reuse discogs_cache_pages table with dummy values (master_id=0, page=0, per_page=0)
        query = text("""
            INSERT INTO discogs_cache_pages (
                cache_key, master_id, page, per_page, response_data, cached_at, expires_at
            )
            VALUES (
                :cache_key, 0, 0, 0, CAST(:response_data AS jsonb),
                NOW(), NOW() + INTERVAL '24 hours'
            )
            ON CONFLICT (cache_key) DO UPDATE SET
                response_data = EXCLUDED.response_data,
                cached_at = NOW(),
                expires_at = NOW() + INTERVAL '24 hours'
        """)

        await self._session.execute(
            query,
            {
                "cache_key": cache_key,
                "response_data": json.dumps(data),
            },
        )
        await self._session.commit()

        logger.info(f"Search cache set: {cache_key}")

    async def invalidate_master(self, master_id: int) -> int:
        """Delete all cached pages for a master."""
        query = text("""
            DELETE FROM discogs_cache_pages
            WHERE master_id = :master_id
        """)

        result = await self._session.execute(
            query, {"master_id": master_id}
        )
        await self._session.commit()

        count = result.rowcount
        logger.info(f"Invalidated {count} cache entries for master {master_id}")
        return count

    async def cleanup_expired(self) -> int:
        """Delete expired cache entries from both tables."""
        # Clean up expired page cache
        page_query = text("""
            DELETE FROM discogs_cache_pages
            WHERE expires_at < NOW()
        """)
        page_result = await self._session.execute(page_query)
        page_count = page_result.rowcount

        # Clean up expired release cache
        release_query = text("""
            DELETE FROM discogs_cache_releases
            WHERE expires_at < NOW()
        """)
        release_result = await self._session.execute(release_query)
        release_count = release_result.rowcount

        await self._session.commit()

        total_count = page_count + release_count
        logger.info(
            f"Cleaned up {total_count} expired cache entries "
            f"({page_count} pages, {release_count} releases)"
        )
        return total_count
