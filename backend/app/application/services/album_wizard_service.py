"""
Album Wizard service.

Handles AI analysis and matching results against the local catalog.
"""

from dataclasses import dataclass
import logging
from typing import Optional
from uuid import UUID

from app.application.ports.album_wizard_client import AlbumWizardClient, AlbumWizardAiResult
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities import Artist, Album


logger = logging.getLogger(__name__)


@dataclass
class AlbumWizardMatch:
    match_status: str
    artist: Optional[Artist]
    album: Optional[Album]


class AlbumWizardService:
    """Service for matching Album Wizard AI output to catalog data."""

    def __init__(self, uow: UnitOfWork, wizard_client: AlbumWizardClient):
        self.uow = uow
        self.wizard_client = wizard_client

    async def analyze_cover(self, image_data_url: str) -> AlbumWizardAiResult:
        return await self.wizard_client.analyze_cover(image_data_url)

    async def match_album(
        self,
        artist_name: Optional[str],
        album_title: Optional[str],
        popular_artist: Optional[str] = None,
        popular_album: Optional[str] = None,
    ) -> AlbumWizardMatch:
        if not artist_name or not artist_name.strip():
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Album Wizard match aborted: empty artist_name")
            return AlbumWizardMatch(match_status="no_artist_match", artist=None, album=None)

        async with self.uow:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Album Wizard match start: artist=%s popular_artist=%s album=%s popular_album=%s",
                    artist_name,
                    popular_artist,
                    album_title,
                    popular_album,
                )
            artist = await self._find_artist_match(artist_name, popular_artist)

            if not artist:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Album Wizard match: no artist match")
                return AlbumWizardMatch(match_status="no_artist_match", artist=None, album=None)

            album = await self._find_album_match(artist.id, album_title)
            if not album and popular_album:
                album = await self._find_album_match(artist.id, popular_album)

            if not album:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "Album Wizard match: no album match for artist_id=%s",
                        artist.id,
                    )
                return AlbumWizardMatch(match_status="no_album_match", artist=artist, album=None)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Album Wizard match: matched artist_id=%s album_id=%s",
                    artist.id,
                    album.id,
                )
            return AlbumWizardMatch(match_status="match_found", artist=artist, album=album)

    async def _find_artist_match(
        self,
        artist_name: Optional[str],
        popular_artist: Optional[str],
    ) -> Optional[Artist]:
        artist = await self._search_artist_contains(artist_name)
        if artist:
            return artist
        return await self._search_artist_contains(popular_artist)

    async def _search_artist_contains(self, query: Optional[str]) -> Optional[Artist]:
        if not query or not query.strip():
            return None
        trimmed = query.strip()
        normalized = trimmed.lower()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Album Wizard artist lookup: query=%s", trimmed)
        candidates, _ = await self.uow.artist_repository.search(
            trimmed,
            limit=5,
            offset=0,
        )
        if not candidates:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Album Wizard artist lookup: no candidates")
            return None
        for candidate in candidates:
            if candidate.name and normalized in candidate.name.strip().lower():
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "Album Wizard artist lookup: contains match id=%s name=%s",
                        candidate.id,
                        candidate.name,
                    )
                return candidate
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Album Wizard artist lookup: fallback match id=%s name=%s",
                candidates[0].id,
                candidates[0].name,
            )
        return candidates[0]

    async def _find_album_match(
        self,
        artist_id: UUID,
        title: Optional[str],
    ) -> Optional[Album]:
        if not title or not title.strip():
            return None

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Album Wizard album lookup: artist_id=%s title=%s",
                artist_id,
                title,
            )
        matches = await self.uow.album_repository.search_by_title_and_artist(
            artist_id,
            title.strip(),
            limit=5
        )
        if not matches:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Album Wizard album lookup: no candidates")
            return None
        normalized = title.strip().lower()
        for candidate in matches:
            if candidate.title and normalized in candidate.title.strip().lower():
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "Album Wizard album lookup: contains match id=%s title=%s",
                        candidate.id,
                        candidate.title,
                    )
                return candidate
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Album Wizard album lookup: fallback match id=%s title=%s",
                matches[0].id,
                matches[0].title,
            )
        return matches[0]
