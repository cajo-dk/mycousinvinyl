"""
Collection import API schemas.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class CollectionImportRowResponse(BaseModel):
    row_number: int
    result: str
    message: str
    discogs_release_id: Optional[int] = None
    artist: Optional[str] = None
    title: Optional[str] = None

    class Config:
        from_attributes = True


class CollectionImportResponse(BaseModel):
    id: UUID
    filename: str
    status: str
    total_rows: int
    processed_rows: int
    success_count: int
    error_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_summary: Optional[str] = None
    rows: Optional[List[CollectionImportRowResponse]] = None

    class Config:
        from_attributes = True


class DiscogsPressingImportRequest(BaseModel):
    release_id: int = Field(..., ge=1)


class DiscogsImportEntityStatusResponse(BaseModel):
    exists: bool
    id: Optional[UUID] = None


class DiscogsPressingImportArtistPreview(BaseModel):
    name: str
    discogs_id: Optional[int] = None
    country: Optional[str] = None
    artist_type: Optional[str] = None
    image_url: Optional[str] = None


class DiscogsPressingImportMasterPreview(BaseModel):
    id: Optional[int] = None
    title: str
    year: Optional[int] = None


class DiscogsPressingImportReleasePreview(BaseModel):
    id: int
    title: str
    year: Optional[int] = None
    country: Optional[str] = None
    label: Optional[str] = None
    catalog_number: Optional[str] = None
    format: Optional[str] = None
    disc_count: Optional[int] = None


class DiscogsPressingImportPreviewResponse(BaseModel):
    artist: DiscogsPressingImportArtistPreview
    master: DiscogsPressingImportMasterPreview
    release: DiscogsPressingImportReleasePreview
    artist_status: DiscogsImportEntityStatusResponse
    album_status: DiscogsImportEntityStatusResponse
    pressing_status: DiscogsImportEntityStatusResponse
    already_in_collection: bool = False
    can_import: bool = True
    warning: Optional[str] = None
