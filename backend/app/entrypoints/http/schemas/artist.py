"""
Artist API schemas.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.domain.value_objects import ArtistType, DataSource


class ArtistBase(BaseModel):
    """Base artist schema with common fields."""
    model_config = {'populate_by_name': True, 'from_attributes': True}

    name: str = Field(..., min_length=1, max_length=500, example="The Beatles")
    sort_name: Optional[str] = Field(None, max_length=500, example="Beatles, The")
    artist_type: str = Field(..., alias='type', example=ArtistType.GROUP)
    country: Optional[str] = Field(None, min_length=2, max_length=2, example="GB", description="ISO 3166-1 alpha-2 country code")
    disambiguation: Optional[str] = Field(None, max_length=500, example="British rock band")
    bio: Optional[str] = Field(None, example="Legendary rock band from Liverpool")
    image_url: Optional[str] = Field(None, description="Data URL or hosted image URL")
    begin_date: Optional[str] = Field(None, example="1960", description="Year or YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, example="1970", description="Year or YYYY-MM-DD format")
    discogs_id: Optional[int] = Field(None, description="Discogs artist ID")
    data_source: DataSource = Field(default=DataSource.USER, example=DataSource.USER)


class ArtistCreate(ArtistBase):
    """Schema for creating a new artist."""
    pass


class ArtistUpdate(BaseModel):
    """Schema for updating an artist (all fields optional)."""
    model_config = {'populate_by_name': True}

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    sort_name: Optional[str] = Field(None, max_length=500)
    artist_type: Optional[str] = Field(None, alias='type')
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    disambiguation: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    image_url: Optional[str] = None
    begin_date: Optional[str] = None
    end_date: Optional[str] = None
    discogs_id: Optional[int] = None


class ArtistResponse(ArtistBase):
    """Schema for artist responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    album_count: Optional[int] = None


class ArtistSummary(BaseModel):
    """Lightweight artist summary for nested responses."""
    model_config = {'populate_by_name': True, 'from_attributes': True}

    id: UUID
    name: str
    artist_type: str = Field(..., alias='type')
    country: Optional[str] = None


class ArtistSearchParams(BaseModel):
    """Query parameters for artist search."""
    query: Optional[str] = Field(None, min_length=1, description="Search query for fuzzy name matching")
    artist_type: Optional[str] = Field(None, description="Filter by artist type")
    country: Optional[str] = Field(None, min_length=2, max_length=2, description="Filter by country code")
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
