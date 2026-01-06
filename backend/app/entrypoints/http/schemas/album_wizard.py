"""
Schemas for Album Wizard AI scan endpoints.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from app.entrypoints.http.schemas.collection_sharing import UserOwnerInfoResponse


class AlbumWizardScanRequest(BaseModel):
    image_data_url: str = Field(..., description="Data URL for the captured album cover image.")


class AlbumWizardAiResult(BaseModel):
    artist: str = Field(..., description="Artist name detected by the AI.")
    album: str = Field(..., description="Album name detected by the AI.")
    image: bool = Field(..., description="Whether the input contained a valid album cover image.")
    artist_confidence: Optional[float] = Field(None, ge=0, le=1)
    album_confidence: Optional[float] = Field(None, ge=0, le=1)
    combined_confidence: Optional[float] = Field(None, ge=0, le=1)
    popular_artist: Optional[str] = None
    popular_album: Optional[str] = None


class AlbumWizardMatchStatus(str, Enum):
    NO_IMAGE = "no_image"
    NO_ARTIST_MATCH = "no_artist_match"
    NO_ALBUM_MATCH = "no_album_match"
    MATCH_FOUND = "match_found"


class AlbumWizardArtistMatch(BaseModel):
    id: str
    name: str
    sort_name: Optional[str] = None
    artist_type: str


class AlbumWizardAlbumMatch(BaseModel):
    id: str
    title: str
    release_year: Optional[int] = None
    image_url: Optional[str] = None


class AlbumWizardScanResponse(BaseModel):
    ai_result: AlbumWizardAiResult
    match_status: AlbumWizardMatchStatus
    matched_artist: Optional[AlbumWizardArtistMatch] = None
    matched_album: Optional[AlbumWizardAlbumMatch] = None
    owners: Optional[List[UserOwnerInfoResponse]] = None
    message: Optional[str] = None
