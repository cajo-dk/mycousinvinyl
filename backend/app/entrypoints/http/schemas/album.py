"""
Album API schemas.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

from app.domain.value_objects import ReleaseType, DataSource, ArtistType
from app.entrypoints.http.schemas.collection_sharing import UserOwnerInfoResponse


class AlbumBase(BaseModel):
    """Base album schema with common fields."""
    model_config = {'populate_by_name': True, 'from_attributes': True}

    title: str = Field(..., min_length=1, max_length=500, example="Abbey Road")
    artist_id: UUID = Field(..., alias='primary_artist_id', description="Primary artist ID")
    release_type: str = Field(..., example=ReleaseType.STUDIO)
    release_year: Optional[int] = Field(None, alias='original_release_year', ge=1900, le=2100, example=1969)
    country_of_origin: Optional[str] = Field(None, min_length=2, max_length=2, example="GB", description="ISO 3166-1 alpha-2 country code")
    genre_ids: List[UUID] = Field(default_factory=list, description="List of genre IDs")
    style_ids: List[UUID] = Field(default_factory=list, description="List of style IDs")
    label: Optional[str] = Field(None, max_length=200, example="Apple Records")
    catalog_number: Optional[str] = Field(None, alias='catalog_number_base', max_length=100, example="PCS 7088")
    notes: Optional[str] = Field(None, alias='description', example="Original UK pressing")
    image_url: Optional[str] = Field(None, description="Data URL or hosted image URL")
    discogs_id: Optional[int] = Field(None, description="Discogs release/master ID")
    data_source: DataSource = Field(default=DataSource.USER, example=DataSource.USER)


class AlbumCreate(AlbumBase):
    """Schema for creating a new album."""
    pass


class AlbumUpdate(BaseModel):
    """Schema for updating an album (all fields optional)."""
    model_config = {'populate_by_name': True}

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    artist_id: Optional[UUID] = Field(None, alias='primary_artist_id')
    release_type: Optional[str] = None
    release_year: Optional[int] = Field(None, alias='original_release_year', ge=1900, le=2100)
    country_of_origin: Optional[str] = Field(None, min_length=2, max_length=2)
    genre_ids: Optional[List[UUID]] = None
    style_ids: Optional[List[UUID]] = None
    label: Optional[str] = Field(None, max_length=200)
    catalog_number: Optional[str] = Field(None, alias='catalog_number_base', max_length=100)
    notes: Optional[str] = Field(None, alias='description')
    image_url: Optional[str] = None
    discogs_id: Optional[int] = None


class GenreSummary(BaseModel):
    """Lightweight genre summary."""
    model_config = {'from_attributes': True}

    id: UUID
    name: str
    display_order: Optional[int] = None


class StyleSummary(BaseModel):
    """Lightweight style summary."""
    model_config = {'from_attributes': True}

    id: UUID
    name: str
    genre_id: Optional[UUID] = None
    display_order: Optional[int] = None


class AlbumResponse(AlbumBase):
    """Schema for album responses with nested data."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    genres: List[GenreSummary] = Field(default_factory=list)
    styles: List[StyleSummary] = Field(default_factory=list)


class AlbumSummary(BaseModel):
    """Lightweight album summary for nested responses."""
    model_config = {'populate_by_name': True, 'from_attributes': True}

    id: UUID
    title: str
    artist_id: UUID = Field(..., alias='primary_artist_id')
    release_year: Optional[int] = Field(None, alias='original_release_year')
    release_type: str


class ArtistSummaryForAlbum(BaseModel):
    """Artist summary for album views."""
    model_config = {'from_attributes': True}

    id: UUID
    name: str
    sort_name: Optional[str] = None
    artist_type: str


class AlbumDetailResponse(BaseModel):
    """Enhanced album response with artist details and pressing count."""
    model_config = {'from_attributes': True}

    id: UUID
    title: str
    artist_id: UUID
    release_year: Optional[int] = None
    release_type: str
    label: Optional[str] = None
    catalog_number: Optional[str] = None
    image_url: Optional[str] = None
    discogs_id: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    styles: List[str] = Field(default_factory=list)
    pressing_count: int = 0
    in_user_collection: bool = Field(
        default=False,
        deprecated=True,
        description="DEPRECATED: Use 'owners' field instead. True if current user owns any pressing of this album."
    )
    owners: Optional[List[UserOwnerInfoResponse]] = Field(
        default=None,
        description="List of owners (current user + followed users with sharing enabled)"
    )
    created_at: datetime
    updated_at: datetime
    # Enriched data
    artist: ArtistSummaryForAlbum


class AlbumSearchParams(BaseModel):
    """Query parameters for album search."""
    query: Optional[str] = Field(None, min_length=1, description="Full-text search query")
    artist_id: Optional[UUID] = Field(None, description="Filter by artist")
    genre_ids: Optional[List[UUID]] = Field(None, description="Filter by genres (OR logic)")
    style_ids: Optional[List[UUID]] = Field(None, description="Filter by styles (OR logic)")
    release_type: Optional[str] = Field(None, description="Filter by release type")
    year_min: Optional[int] = Field(None, ge=1900, le=2100, description="Minimum release year")
    year_max: Optional[int] = Field(None, ge=1900, le=2100, description="Maximum release year")
    sort_by: str = Field(default="relevance", description="Sort field: relevance, title, year_desc, year_asc")
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
