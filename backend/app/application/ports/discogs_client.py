"""
Port interface for Discogs integration.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TypedDict


class DiscogsArtistSearchResult(TypedDict):
    id: int
    name: str
    thumb_url: Optional[str]
    uri: Optional[str]
    resource_url: Optional[str]


class DiscogsArtistDetails(TypedDict):
    id: int
    name: str
    bio: Optional[str]
    country: Optional[str]
    begin_date: Optional[str]
    end_date: Optional[str]
    sort_name: Optional[str]
    image_url: Optional[str]
    artist_type: Optional[str]


class DiscogsAlbumSearchResult(TypedDict):
    id: int
    title: str
    year: Optional[int]
    type: Optional[str]
    thumb_url: Optional[str]
    resource_url: Optional[str]


class DiscogsAlbumDetails(TypedDict):
    id: int
    title: str
    year: Optional[int]
    country: Optional[str]
    genres: Optional[list[str]]
    styles: Optional[list[str]]
    label: Optional[str]
    catalog_number: Optional[str]
    image_url: Optional[str]
    type: Optional[str]


class DiscogsReleaseSearchResult(TypedDict):
    id: int
    title: str
    year: Optional[int]
    country: Optional[str]
    label: Optional[str]
    format: Optional[str]
    type: str
    master_id: Optional[int]
    master_title: Optional[str]
    thumb_url: Optional[str]
    resource_url: Optional[str]


class DiscogsReleaseSearchResponse(TypedDict):
    items: List[DiscogsReleaseSearchResult]
    total: Optional[int]


class DiscogsReleaseDetails(TypedDict):
    id: int
    title: str
    year: Optional[int]
    country: Optional[str]
    label: Optional[str]
    catalog_number: Optional[str]
    barcode: Optional[str]
    identifiers: Optional[str]
    image_url: Optional[str]
    formats: Optional[list[str]]
    format_descriptions: Optional[list[str]]
    disc_count: Optional[int]
    master_id: Optional[int]
    master_title: Optional[str]
    pressing_plant: Optional[str]
    mastering_engineer: Optional[str]
    mastering_studio: Optional[str]
    vinyl_color: Optional[str]
    edition_type: Optional[str]
    sleeve_type: Optional[str]


class DiscogsPriceSuggestions(TypedDict):
    min_value: float
    median_value: float
    max_value: float
    currency: str


class DiscogsClient(ABC):
    """Abstract client for Discogs microservice."""

    @abstractmethod
    async def search_artists(self, query: str, limit: int = 3) -> List[DiscogsArtistSearchResult]:
        raise NotImplementedError

    @abstractmethod
    async def get_artist(self, artist_id: int) -> DiscogsArtistDetails:
        raise NotImplementedError

    @abstractmethod
    async def search_albums(self, artist_id: int, query: str, limit: int = 3) -> list[DiscogsAlbumSearchResult]:
        raise NotImplementedError

    @abstractmethod
    async def get_album(self, album_id: int, album_type: str) -> DiscogsAlbumDetails:
        raise NotImplementedError

    @abstractmethod
    async def get_master_releases(self, master_id: int, page: int = 1, per_page: int = 25) -> DiscogsReleaseSearchResponse:
        raise NotImplementedError

    @abstractmethod
    async def search_master_releases(self, master_id: int, query: str, limit: int = 25) -> DiscogsReleaseSearchResponse:
        """Search for releases under a master by query string."""
        raise NotImplementedError

    @abstractmethod
    async def get_release(self, release_id: int) -> DiscogsReleaseDetails:
        raise NotImplementedError

    @abstractmethod
    async def get_price_suggestions(self, release_id: int) -> Optional[DiscogsPriceSuggestions]:
        """
        Fetch marketplace price suggestions for a release.

        Returns dict with min_value, median_value, max_value, currency.
        Returns None if pricing not available.
        """
        raise NotImplementedError
