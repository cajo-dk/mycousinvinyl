"""
Lookup data API schemas (genres, styles, countries).

Admin-focused schemas for managing reference data.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# GENRE SCHEMAS
# ============================================================================

class GenreBase(BaseModel):
    """Base genre schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, example="Rock")
    display_order: Optional[int] = Field(None, ge=0, example=1)


class GenreCreate(GenreBase):
    """Schema for creating a new genre."""
    pass


class GenreUpdate(GenreBase):
    """Schema for updating a genre."""
    pass


class GenreResponse(GenreBase):
    """Schema for genre responses."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# STYLE SCHEMAS
# ============================================================================

class StyleBase(BaseModel):
    """Base style schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, example="Progressive Rock")
    genre_id: Optional[UUID] = Field(None, description="Parent genre ID (optional)")
    display_order: Optional[int] = Field(None, ge=0, example=1)


class StyleCreate(StyleBase):
    """Schema for creating a new style."""
    pass


class StyleUpdate(StyleBase):
    """Schema for updating a style."""
    pass


class StyleResponse(StyleBase):
    """Schema for style responses."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# COUNTRY SCHEMAS
# ============================================================================

class CountryBase(BaseModel):
    """Base country schema with common fields."""
    code: str = Field(..., min_length=2, max_length=2, example="GB", description="ISO 3166-1 alpha-2 code")
    name: str = Field(..., min_length=1, max_length=100, example="United Kingdom")
    display_order: Optional[int] = Field(None, ge=0, example=1)


class CountryCreate(CountryBase):
    """Schema for creating a new country."""
    pass


class CountryUpdate(BaseModel):
    """Schema for updating a country (code is immutable)."""
    name: str = Field(..., min_length=1, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)


class CountryResponse(CountryBase):
    """Schema for country responses."""
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ARTIST TYPE SCHEMAS
# ============================================================================

class ArtistTypeBase(BaseModel):
    """Base artist type schema with common fields."""
    code: str = Field(..., min_length=1, max_length=50, example="Person")
    name: str = Field(..., min_length=1, max_length=100, example="Person")
    display_order: Optional[int] = Field(None, ge=0, example=1)


class ArtistTypeCreate(ArtistTypeBase):
    """Schema for creating a new artist type."""
    pass


class ArtistTypeUpdate(BaseModel):
    """Schema for updating an artist type (code is immutable)."""
    name: str = Field(..., min_length=1, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)


class ArtistTypeResponse(ArtistTypeBase):
    """Schema for artist type responses."""
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# RELEASE TYPE SCHEMAS
# ============================================================================

class ReleaseTypeBase(BaseModel):
    """Base release type schema with common fields."""
    code: str = Field(..., min_length=1, max_length=50, example="Studio")
    name: str = Field(..., min_length=1, max_length=100, example="Studio")
    display_order: Optional[int] = Field(None, ge=0, example=1)


class ReleaseTypeCreate(ReleaseTypeBase):
    """Schema for creating a new release type."""
    pass


class ReleaseTypeUpdate(BaseModel):
    """Schema for updating a release type (code is immutable)."""
    name: str = Field(..., min_length=1, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)


class ReleaseTypeResponse(ReleaseTypeBase):
    """Schema for release type responses."""
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# EDITION TYPE SCHEMAS
# ============================================================================

class EditionTypeBase(BaseModel):
    """Base edition type schema with common fields."""
    code: str = Field(..., min_length=1, max_length=50, example="Standard")
    name: str = Field(..., min_length=1, max_length=100, example="Standard")
    display_order: Optional[int] = Field(None, ge=0, example=1)


class EditionTypeCreate(EditionTypeBase):
    """Schema for creating a new edition type."""
    pass


class EditionTypeUpdate(BaseModel):
    """Schema for updating an edition type (code is immutable)."""
    name: str = Field(..., min_length=1, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)


class EditionTypeResponse(EditionTypeBase):
    """Schema for edition type responses."""
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SLEEVE TYPE SCHEMAS
# ============================================================================

class SleeveTypeBase(BaseModel):
    """Base sleeve type schema with common fields."""
    code: str = Field(..., min_length=1, max_length=50, example="Gatefold")
    name: str = Field(..., min_length=1, max_length=100, example="Gatefold")
    display_order: Optional[int] = Field(None, ge=0, example=1)


class SleeveTypeCreate(SleeveTypeBase):
    """Schema for creating a new sleeve type."""
    pass


class SleeveTypeUpdate(BaseModel):
    """Schema for updating a sleeve type (code is immutable)."""
    name: str = Field(..., min_length=1, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)


class SleeveTypeResponse(SleeveTypeBase):
    """Schema for sleeve type responses."""
    created_at: datetime

    class Config:
        from_attributes = True
