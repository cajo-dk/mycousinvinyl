"""
Service for Discogs integration.
"""

import logging
from typing import List

from app.application.ports.discogs_client import (
    DiscogsClient,
    DiscogsArtistSearchResult,
    DiscogsArtistDetails,
    DiscogsAlbumSearchResult,
    DiscogsAlbumDetails,
    DiscogsReleaseSearchResult,
    DiscogsReleaseSearchResponse,
    DiscogsReleaseDetails,
)
from app.application.ports.discogs_cache_repository import DiscogsCacheRepository

logger = logging.getLogger(__name__)


class DiscogsService:
    """Application service that proxies Discogs microservice calls."""

    def __init__(self, client: DiscogsClient, cache_repo: DiscogsCacheRepository):
        self._client = client
        self._cache = cache_repo

    async def search_artists(self, query: str, limit: int = 3) -> List[DiscogsArtistSearchResult]:
        return await self._client.search_artists(query=query, limit=limit)

    async def get_artist(self, artist_id: int) -> DiscogsArtistDetails:
        return await self._client.get_artist(artist_id)

    async def search_albums(self, artist_id: int, query: str, limit: int = 10, page: int = 1) -> dict:
        response = await self._client.search_albums(artist_id=artist_id, query=query, limit=limit, page=page)
        return response

    async def get_album(self, album_id: int, album_type: str) -> DiscogsAlbumDetails:
        return await self._client.get_album(album_id, album_type)

    async def get_master_releases(self, master_id: int, page: int = 1, per_page: int = 25) -> DiscogsReleaseSearchResponse:
        # Try cache first
        cached = await self._cache.get_page_cache(master_id, page, per_page)
        if cached:
            logger.info(f"Cache hit: master={master_id}, page={page}")
            return cached

        # Cache miss - fetch from Discogs
        logger.info(f"Cache miss: master={master_id}, page={page}")
        response = await self._client.get_master_releases(master_id=master_id, page=page, per_page=per_page)

        # Cache page data
        await self._cache.set_page_cache(master_id, page, per_page, response)

        return response

    async def search_master_releases(self, master_id: int, query: str, limit: int = 25) -> DiscogsReleaseSearchResponse:
        """Search for releases under a master with caching."""
        # Build cache key: search:{master_id}:{query_normalized}:{limit}
        cache_key = f"search:{master_id}:{query.lower().strip()}:{limit}"

        # Try cache first
        cached = await self._cache.get_search_cache(cache_key)
        if cached:
            logger.info(f"Search cache hit: {cache_key}")
            return cached

        # Cache miss - fetch from Discogs
        logger.info(f"Search cache miss: {cache_key}")
        response = await self._client.search_master_releases(
            master_id=master_id, query=query, limit=limit
        )

        # Cache search results
        await self._cache.set_search_cache(cache_key, response)

        return response

    async def get_release(self, release_id: int) -> DiscogsReleaseDetails:
        # Try cache first
        cached = await self._cache.get_release_cache(release_id)
        if cached:
            logger.debug(f"Release cache hit: {release_id}")
            return cached

        # Cache miss - fetch from Discogs
        logger.debug(f"Release cache miss: {release_id}")
        release = await self._client.get_release(release_id)

        # Cache release data
        await self._cache.set_release_cache(release_id, release)

        return release
