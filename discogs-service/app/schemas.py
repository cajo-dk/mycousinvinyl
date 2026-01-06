from typing import List, Optional
from pydantic import BaseModel


class DiscogsArtistSearchResult(BaseModel):
    id: int
    name: str
    thumb_url: Optional[str] = None
    uri: Optional[str] = None
    resource_url: Optional[str] = None


class DiscogsArtistSearchResponse(BaseModel):
    items: List[DiscogsArtistSearchResult]


class DiscogsArtistDetails(BaseModel):
  id: int
  name: str
  bio: Optional[str] = None
  country: Optional[str] = None
  begin_date: Optional[str] = None
  end_date: Optional[str] = None
  sort_name: Optional[str] = None
  image_url: Optional[str] = None
  artist_type: Optional[str] = None


class DiscogsAlbumSearchResult(BaseModel):
  id: int
  title: str
  year: Optional[int] = None
  type: Optional[str] = None
  thumb_url: Optional[str] = None
  resource_url: Optional[str] = None


class DiscogsAlbumSearchResponse(BaseModel):
  items: List[DiscogsAlbumSearchResult]
  total: Optional[int] = None
  page: Optional[int] = None
  pages: Optional[int] = None


class DiscogsAlbumDetails(BaseModel):
  id: int
  title: str
  year: Optional[int] = None
  country: Optional[str] = None
  genres: Optional[List[str]] = None
  styles: Optional[List[str]] = None
  label: Optional[str] = None
  catalog_number: Optional[str] = None
  image_url: Optional[str] = None
  type: Optional[str] = None


class DiscogsReleaseSearchResult(BaseModel):
  id: int
  title: str
  year: Optional[int] = None
  country: Optional[str] = None
  label: Optional[str] = None
  format: Optional[str] = None
  type: str
  master_id: Optional[int] = None
  master_title: Optional[str] = None
  thumb_url: Optional[str] = None
  resource_url: Optional[str] = None


class DiscogsReleaseSearchResponse(BaseModel):
  items: List[DiscogsReleaseSearchResult]
  total: Optional[int] = None


class DiscogsReleaseDetails(BaseModel):
  id: int
  title: str
  year: Optional[int] = None
  country: Optional[str] = None
  genres: Optional[List[str]] = None
  styles: Optional[List[str]] = None
  label: Optional[str] = None
  catalog_number: Optional[str] = None
  barcode: Optional[str] = None
  identifiers: Optional[str] = None
  image_url: Optional[str] = None
  formats: Optional[List[str]] = None
  format_descriptions: Optional[List[str]] = None
  disc_count: Optional[int] = None
  master_id: Optional[int] = None
  master_title: Optional[str] = None
  pressing_plant: Optional[str] = None
  mastering_engineer: Optional[str] = None
  mastering_studio: Optional[str] = None
  vinyl_color: Optional[str] = None
  edition_type: Optional[str] = None
  sleeve_type: Optional[str] = None


class DiscogsPriceSuggestionsResponse(BaseModel):
  """Price suggestions response from Discogs marketplace API."""
  min_value: Optional[float] = None
  median_value: Optional[float] = None
  max_value: Optional[float] = None
  currency: Optional[str] = None
