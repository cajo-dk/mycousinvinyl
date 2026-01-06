"""
Port interface for Album Wizard AI integration.
"""

from abc import ABC, abstractmethod
from typing import Optional, TypedDict


class AlbumWizardAiResult(TypedDict):
    artist: str
    album: str
    image: bool
    artist_confidence: Optional[float]
    album_confidence: Optional[float]
    combined_confidence: Optional[float]
    popular_artist: Optional[str]
    popular_album: Optional[str]


class AlbumWizardClient(ABC):
    """Abstract client for the Album Wizard AI."""

    @abstractmethod
    async def analyze_cover(self, image_data_url: str) -> AlbumWizardAiResult:
        raise NotImplementedError
