"""
Collection API schemas.

SECURITY NOTE: user_id is never included in request schemas - it's always
extracted from the authenticated user context.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, condecimal

from app.domain.value_objects import Condition


class CollectionItemBase(BaseModel):
    """Base collection item schema (for requests)."""
    model_config = {'populate_by_name': True, 'from_attributes': True}

    pressing_id: UUID = Field(..., description="Pressing ID to add to collection")
    media_condition: Condition = Field(..., example=Condition.NEAR_MINT, description="Vinyl condition")
    sleeve_condition: Condition = Field(..., example=Condition.VG_PLUS, description="Sleeve condition")
    purchase_price: Optional[condecimal(ge=Decimal('0'), decimal_places=2)] = Field(
        None, example=Decimal('25.99'), description="Purchase price"
    )
    purchase_currency: Optional[str] = Field(
        None, min_length=3, max_length=3, example="DKK", description="ISO 4217 currency code"
    )
    purchase_date: Optional[date] = Field(None, example="2024-01-15")
    seller: Optional[str] = Field(None, max_length=200, example="Discogs seller")
    location: Optional[str] = Field(
        None,
        max_length=200,
        example="Shelf A3",
        alias="storage_location",
        serialization_alias="location",
    )
    defect_notes: Optional[str] = Field(None, example="Minor scuff on side B")
    notes: Optional[str] = Field(
        None,
        example="First pressing with poster",
        alias="user_notes",
        serialization_alias="notes",
    )


class CollectionItemCreate(CollectionItemBase):
    """Schema for adding item to collection."""
    pass


class CollectionItemUpdate(BaseModel):
    """Schema for updating collection item (all fields optional)."""
    model_config = {'populate_by_name': True}

    media_condition: Optional[Condition] = None
    sleeve_condition: Optional[Condition] = None
    purchase_price: Optional[condecimal(ge=Decimal('0'), decimal_places=2)] = None
    purchase_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    purchase_date: Optional[date] = None
    seller: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(
        None,
        max_length=200,
        alias="storage_location",
        serialization_alias="location",
    )
    defect_notes: Optional[str] = None
    notes: Optional[str] = Field(None, alias="user_notes", serialization_alias="notes")


class ConditionUpdateRequest(BaseModel):
    """Schema for updating condition-specific fields."""
    media_condition: Optional[Condition] = None
    sleeve_condition: Optional[Condition] = None
    defect_notes: Optional[str] = None


class PurchaseInfoUpdateRequest(BaseModel):
    """Schema for updating purchase information."""
    purchase_price: Optional[condecimal(ge=Decimal('0'), decimal_places=2)] = None
    purchase_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    purchase_date: Optional[date] = None
    seller: Optional[str] = Field(None, max_length=200)


class RatingUpdateRequest(BaseModel):
    """Schema for updating rating and notes."""
    rating: int = Field(..., ge=0, le=5, example=5, description="Rating from 0-5")
    notes: Optional[str] = Field(None, example="Classic album, sounds amazing")


class CollectionItemResponse(CollectionItemBase):
    """Schema for collection item responses."""
    id: UUID
    user_id: UUID
    rating: Optional[int] = Field(None, ge=0, le=5)
    play_count: int = Field(default=0, ge=0)
    last_played: Optional[datetime] = None
    date_added: datetime
    updated_at: datetime


class ArtistSummary(BaseModel):
    """Lightweight artist summary for collection views."""
    id: UUID
    name: str
    sort_name: Optional[str] = None
    country: Optional[str] = None

    class Config:
        from_attributes = True


class AlbumSummary(BaseModel):
    """Lightweight album summary for collection views."""
    id: UUID
    title: str
    release_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class MarketDataSummary(BaseModel):
    """Market pricing data summary."""
    min_value: Optional[Decimal] = None
    median_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    currency: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CollectionItemDetailResponse(BaseModel):
    """Enhanced collection item response with artist and album details."""
    model_config = {'populate_by_name': True, 'from_attributes': True}

    id: UUID
    user_id: UUID
    pressing_id: UUID
    pressing_image_url: Optional[str] = None
    media_condition: Condition
    sleeve_condition: Condition
    purchase_price: Optional[Decimal] = None
    purchase_currency: Optional[str] = None
    purchase_date: Optional[date] = None
    seller: Optional[str] = None
    location: Optional[str] = Field(None, alias="storage_location", serialization_alias="location")
    defect_notes: Optional[str] = None
    notes: Optional[str] = Field(None, alias="user_notes", serialization_alias="notes")
    rating: Optional[int] = Field(None, ge=0, le=5)
    play_count: int = Field(default=0, ge=0)
    last_played: Optional[datetime] = None
    date_added: datetime
    updated_at: datetime
    # Enriched data
    artist: ArtistSummary
    album: AlbumSummary
    market_data: Optional[MarketDataSummary] = None


class CollectionItemSummary(BaseModel):
    """Lightweight collection item summary."""
    model_config = {'from_attributes': True}

    id: UUID
    pressing_id: UUID
    media_condition: Condition
    sleeve_condition: Condition
    date_added: datetime


class CollectionSearchParams(BaseModel):
    """Query parameters for collection search and filtering."""
    query: Optional[str] = Field(None, min_length=1, description="Search album titles and artists")
    media_conditions: Optional[List[Condition]] = Field(None, description="Filter by media conditions (OR logic)")
    sleeve_conditions: Optional[List[Condition]] = Field(None, description="Filter by sleeve conditions (OR logic)")
    rating_min: Optional[int] = Field(None, ge=0, le=5, description="Minimum rating")
    rating_max: Optional[int] = Field(None, ge=0, le=5, description="Maximum rating")
    price_min: Optional[Decimal] = Field(None, ge=0, description="Minimum purchase price")
    price_max: Optional[Decimal] = Field(None, ge=0, description="Maximum purchase price")
    sort_by: str = Field(
        default="date_added_desc",
        description="Sort field: date_added_desc, date_added_asc, artist, album, rating_desc, price_desc"
    )
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class TopArtistEntry(BaseModel):
    """Top artist entry for collection statistics."""
    artist_id: UUID
    artist_name: str
    collected_count: int


class TopAlbumEntry(BaseModel):
    """Top album entry for collection statistics."""
    album_id: UUID
    album_title: str
    artist_id: UUID
    artist_name: str
    collected_count: int


class CollectionStatistics(BaseModel):
    """Collection statistics response."""
    total_albums: int = Field(..., example=150)
    total_purchase_price: float = Field(..., example=3500.00)
    min_value: float = Field(..., example=5.00)
    avg_value: float = Field(..., example=23.33)
    max_value: float = Field(..., example=150.00)
    low_est_sales_price: float = Field(..., example=2800.00)
    avg_est_sales_price: float = Field(..., example=4200.00)
    high_est_sales_price: float = Field(..., example=6500.00)
    currency: str = Field(..., example="DKK")
    top_artists: List[TopArtistEntry] = Field(default_factory=list)
    top_albums: List[TopAlbumEntry] = Field(default_factory=list)

    class Config:
        from_attributes = True


class AlbumPlayIncrementResponse(BaseModel):
    """Response for incrementing album play count."""
    album_id: UUID
    play_count: int
    play_count_ytd: int
    last_played_at: datetime


class PlayedAlbumEntry(BaseModel):
    """Played album entry for YTD stats."""
    album_id: UUID
    album_title: str
    artist_id: UUID
    artist_name: str
    play_count_ytd: int
    last_played_at: Optional[datetime] = None
