"""
HTTP adapter for the Discogs microservice. 
"""

from typing import List, Optional
import httpx

from app.application.ports.discogs_client import (
    DiscogsClient,
    DiscogsArtistSearchResult,
    DiscogsArtistDetails,
    DiscogsAlbumSearchResult,
    DiscogsAlbumDetails,
    DiscogsReleaseSearchResult,
    DiscogsReleaseSearchResponse,
    DiscogsReleaseDetails,
    DiscogsPriceSuggestions,
)


class DiscogsClientAdapter(DiscogsClient):
    def __init__(self, base_url: str, timeout_seconds: float = 10.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def search_artists(self, query: str, limit: int = 3) -> List[DiscogsArtistSearchResult]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/artists/search",
                params={"query": query, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])

    async def get_artist(self, artist_id: int) -> DiscogsArtistDetails:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/artists/{artist_id}")
            response.raise_for_status()
            return response.json()

    async def search_albums(self, artist_id: int, query: str, limit: int = 10, page: int = 1) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/albums/search",
                params={"artist_id": artist_id, "query": query, "limit": limit, "page": page},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "items": data.get("items", []),
                "total": data.get("total"),
                "page": data.get("page"),
                "pages": data.get("pages"),
            }

    async def get_album(self, album_id: int, album_type: str) -> DiscogsAlbumDetails:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/albums/{album_id}",
                params={"type": album_type},
            )
            response.raise_for_status()
            return response.json()

    async def get_master_releases(self, master_id: int, page: int = 1, per_page: int = 25) -> DiscogsReleaseSearchResponse:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/masters/{master_id}/releases",
                params={"page": page, "limit": per_page},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "items": data.get("items", []),
                "total": data.get("total"),
                "page": data.get("page"),
                "pages": data.get("pages"),
            }

    async def search_master_releases(self, master_id: int, query: str, limit: int = 25) -> DiscogsReleaseSearchResponse:
        """Search for releases under a master via discogs-service."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/masters/{master_id}/search",
                params={"q": query, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "items": data.get("items", []),
                "total": data.get("total", 0),
            }

    async def get_release(self, release_id: int) -> DiscogsReleaseDetails:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/releases/{release_id}")
            response.raise_for_status()
            return response.json()

    async def get_price_suggestions(self, release_id: int) -> Optional[DiscogsPriceSuggestions]:
        """Fetch price suggestions from discogs-service."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(
                    f"{self._base_url}/marketplace/price_suggestions/{release_id}"
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (401, 403):
                    return None
                if exc.response.status_code == 404:
                    # No pricing data available
                    return None
                raise
