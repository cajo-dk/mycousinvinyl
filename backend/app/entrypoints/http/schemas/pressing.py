"""
Pressing, Matrix, and Packaging API schemas.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.domain.value_objects import (
    VinylFormat, VinylSpeed, VinylSize, EditionType, SleeveType
)
from app.entrypoints.http.schemas.collection_sharing import UserOwnerInfoResponse


# ============================================================================
# MATRIX SCHEMAS
# ============================================================================

class MatrixBase(BaseModel):
    """Base matrix schema with common fields."""
    pressing_id: UUID = Field(..., description="Pressing ID this matrix belongs to")
    side: str = Field(..., min_length=1, max_length=10, example="A")
    matrix_code: Optional[str] = Field(None, max_length=200, example="YEX 749-1")
    etchings: Optional[str] = Field(None, max_length=500, example="Hand-etched text")
    stamper_info: Optional[str] = Field(None, max_length=200, example="Stamper G")


class MatrixCreate(MatrixBase):
    """Schema for creating a matrix code."""
    pass


class MatrixResponse(MatrixBase):
    """Schema for matrix responses."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MatrixBulkUpdate(BaseModel):
    """Schema for bulk matrix update (replaces all matrices for a pressing)."""
    matrices: List[MatrixBase] = Field(..., description="Complete list of matrices for pressing")


# ============================================================================
# PACKAGING SCHEMAS
# ============================================================================

class PackagingBase(BaseModel):
    """Base packaging schema with common fields."""
    pressing_id: UUID = Field(..., description="Pressing ID this packaging belongs to")
    sleeve_type: str = Field(..., example=SleeveType.GATEFOLD)
    has_inner_sleeve: bool = Field(default=False, example=True)
    inner_sleeve_description: Optional[str] = Field(None, max_length=500, example="Original photo inner")
    has_insert: bool = Field(default=False, example=True)
    insert_description: Optional[str] = Field(None, max_length=500, example="Lyric insert")
    has_poster: bool = Field(default=False, example=False)
    poster_description: Optional[str] = Field(None, max_length=500)
    sticker_info: Optional[str] = Field(None, max_length=500, example="Hype sticker on shrink wrap")
    notes: Optional[str] = Field(None, example="Complete with all original inserts")


class PackagingCreateOrUpdate(PackagingBase):
    """Schema for creating or updating packaging (upsert operation)."""
    pass


class PackagingResponse(PackagingBase):
    """Schema for packaging responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PRESSING SCHEMAS
# ============================================================================

class PressingBase(BaseModel):
    """Base pressing schema with common fields."""
    model_config = {'populate_by_name': True, 'from_attributes': True}

    album_id: UUID = Field(..., description="Album ID this pressing belongs to")
    format: VinylFormat = Field(..., example=VinylFormat.LP)
    speed_rpm: VinylSpeed = Field(..., example=VinylSpeed.RPM_33)
    size_inches: VinylSize = Field(..., example=VinylSize.SIZE_12)
    disc_count: int = Field(default=1, ge=1, le=10, example=1)
    country: Optional[str] = Field(None, alias='pressing_country', min_length=2, max_length=2, example="GB", description="ISO country code")
    release_year: Optional[int] = Field(None, alias='pressing_year', ge=1900, le=2100, example=1969)
    pressing_plant: Optional[str] = Field(None, max_length=200, example="EMI Hayes")
    mastering_engineer: Optional[str] = Field(None, max_length=200, example="Bob Ludwig")
    mastering_studio: Optional[str] = Field(None, max_length=200, example="Abbey Road Studios")
    vinyl_color: Optional[str] = Field(None, max_length=100, example="Black")
    label_design: Optional[str] = Field(None, max_length=200, example="Apple label")
    image_url: Optional[str] = Field(None, description="Cover image URL or data URL for this pressing")
    edition_type: Optional[str] = Field(None, example=EditionType.STANDARD)
    barcode: Optional[str] = Field(None, max_length=2000)
    notes: Optional[str] = Field(None, example="Original UK pressing with 'Her Majesty' runout")
    discogs_release_id: Optional[int] = Field(None, description="Discogs release ID")
    discogs_master_id: Optional[int] = Field(None, description="Discogs master ID")
    master_title: Optional[str] = Field(None, max_length=500, description="Discogs master release title")


class PressingCreate(PressingBase):
    """Schema for creating a new pressing."""
    import_master_releases: Optional[bool] = Field(
        None,
        description="If true, enqueue creation of all releases under the Discogs master"
    )


class PressingUpdate(BaseModel):
    """Schema for updating a pressing (all fields optional)."""
    model_config = {'populate_by_name': True}

    format: Optional[VinylFormat] = None
    speed_rpm: Optional[VinylSpeed] = None
    size_inches: Optional[VinylSize] = None
    disc_count: Optional[int] = Field(None, ge=1, le=10)
    country: Optional[str] = Field(None, alias='pressing_country', min_length=2, max_length=2)
    release_year: Optional[int] = Field(None, alias='pressing_year', ge=1900, le=2100)
    pressing_plant: Optional[str] = Field(None, max_length=200)
    mastering_engineer: Optional[str] = Field(None, max_length=200)
    mastering_studio: Optional[str] = Field(None, max_length=200)
    vinyl_color: Optional[str] = Field(None, max_length=100)
    label_design: Optional[str] = Field(None, max_length=200)
    image_url: Optional[str] = None
    edition_type: Optional[str] = None
    barcode: Optional[str] = Field(None, max_length=2000)
    notes: Optional[str] = None
    discogs_release_id: Optional[int] = None
    discogs_master_id: Optional[int] = None
    master_title: Optional[str] = Field(None, max_length=500)


class PressingResponse(PressingBase):
    """Schema for pressing responses."""
    id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    matrices: List[MatrixResponse] = Field(default_factory=list)
    packaging: Optional[PackagingResponse] = None
    is_master: Optional[bool] = None
    in_user_collection: bool = Field(
        default=False,
        deprecated=True,
        description="DEPRECATED: Use 'owners' field instead. True if current user owns this pressing."
    )
    owners: Optional[List[UserOwnerInfoResponse]] = Field(
        default=None,
        description="List of owners (current user + followed users with sharing enabled)"
    )


class PressingSummary(BaseModel):
    """Lightweight pressing summary for nested responses."""
    model_config = {'populate_by_name': True, 'from_attributes': True}

    id: UUID
    format: VinylFormat
    speed_rpm: VinylSpeed
    size_inches: VinylSize
    country: Optional[str] = Field(None, alias='pressing_country')
    release_year: Optional[int] = Field(None, alias='pressing_year')
    image_url: Optional[str] = None


class PressingSearchParams(BaseModel):
    """Query parameters for pressing search."""
    album_id: Optional[UUID] = Field(None, description="Filter by album")
    format: Optional[VinylFormat] = Field(None, description="Filter by format")
    speed_rpm: Optional[VinylSpeed] = Field(None, description="Filter by speed")
    size_inches: Optional[VinylSize] = Field(None, description="Filter by size")
    country: Optional[str] = Field(None, min_length=2, max_length=2, description="Filter by country")
    year_min: Optional[int] = Field(None, ge=1900, le=2100, description="Minimum release year")
    year_max: Optional[int] = Field(None, ge=1900, le=2100, description="Maximum release year")
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# ============================================================================
# ENRICHED DETAIL SCHEMAS (for hierarchical display)
# ============================================================================

class ArtistSummaryForPressing(BaseModel):
    """Artist summary for pressing views."""
    model_config = {'from_attributes': True}

    id: UUID
    name: str
    sort_name: Optional[str] = None
    discogs_id: Optional[int] = None


class AlbumSummaryForPressing(BaseModel):
    """Album summary for pressing views."""
    model_config = {'from_attributes': True}

    id: UUID
    title: str
    release_year: Optional[int] = None
    image_url: Optional[str] = None
    discogs_id: Optional[int] = None


class PressingDetailResponse(BaseModel):
    """Enhanced pressing response with artist and album details."""
    model_config = {'from_attributes': True}

    id: UUID
    album_id: UUID
    format: VinylFormat
    speed_rpm: VinylSpeed
    size_inches: VinylSize
    disc_count: int
    country: Optional[str] = None
    release_year: Optional[int] = None
    pressing_plant: Optional[str] = None
    vinyl_color: Optional[str] = None
    edition_type: Optional[str] = None
    sleeve_type: Optional[str] = None
    barcode: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
    discogs_release_id: Optional[int] = None
    discogs_master_id: Optional[int] = None
    master_title: Optional[str] = None
    is_master: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    # Enriched data
    artist: ArtistSummaryForPressing
    album: AlbumSummaryForPressing
    in_user_collection: bool = False
