"""
Collection import API schemas.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


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
