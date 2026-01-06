"""
Track API schemas.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class TrackBase(BaseModel):
    """Base track schema with common fields."""
    album_id: UUID = Field(..., description="Album ID this track belongs to")
    side: str = Field(..., min_length=1, max_length=10, example="A", description="Side designation (A, B, 1, 2, etc.)")
    position: str = Field(..., min_length=1, max_length=10, example="1", description="Track position on side")
    title: str = Field(..., min_length=1, max_length=500, example="Come Together")
    duration: Optional[int] = Field(None, ge=0, example=259, description="Duration in seconds")
    credits: Optional[str] = Field(None, example="Lennon/McCartney")


class TrackCreate(TrackBase):
    """Schema for creating a new track."""
    pass


class TrackUpdate(BaseModel):
    """Schema for updating a track (all fields optional)."""
    side: Optional[str] = Field(None, min_length=1, max_length=10)
    position: Optional[str] = Field(None, min_length=1, max_length=10)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    duration: Optional[int] = Field(None, ge=0)
    credits: Optional[str] = None


class TrackResponse(TrackBase):
    """Schema for track responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrackReorderItem(BaseModel):
    """Schema for track reordering item."""
    track_id: UUID
    side: str = Field(..., min_length=1, max_length=10)
    position: str = Field(..., min_length=1, max_length=10)


class TrackReorderRequest(BaseModel):
    """Schema for bulk track reordering."""
    tracks: List[TrackReorderItem] = Field(..., min_items=1, description="List of tracks with new positions")


class TrackSummary(BaseModel):
    """Lightweight track summary for nested responses."""
    id: UUID
    side: str
    position: str
    title: str
    duration: Optional[int] = None

    class Config:
        from_attributes = True
