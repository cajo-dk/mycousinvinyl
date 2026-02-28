"""
Discogs tracklist synchronization service.
"""

import re
from typing import Any, Optional
from uuid import UUID

from app.application.services.album_service import AlbumService
from app.application.services.discogs_service import DiscogsService
from app.application.services.track_service import TrackService


class DiscogsTracklistSyncService:
    """Synchronize album tracks from Discogs data."""

    def __init__(
        self,
        album_service: AlbumService,
        discogs_service: DiscogsService,
        track_service: TrackService,
    ):
        self.album_service = album_service
        self.discogs_service = discogs_service
        self.track_service = track_service

    async def sync_album(self, album_id: UUID, discogs_id: Optional[int]) -> int:
        """Sync a single album tracklist from Discogs and return imported track count."""
        if not discogs_id:
            raise ValueError("Album must have a Discogs ID before syncing tracks")

        details: dict[str, Any]
        try:
            details = await self.discogs_service.get_album(discogs_id, "master")
        except Exception:
            details = await self.discogs_service.get_album(discogs_id, "release")

        raw_tracklist = details.get("tracklist") if isinstance(details, dict) else None
        tracks_to_store = self._normalize_discogs_tracklist(raw_tracklist or [])
        if not tracks_to_store:
            raise ValueError("Discogs did not return any importable tracks for this album")

        created = await self.track_service.replace_album_tracks(album_id, tracks_to_store)
        return len(created)

    async def sync_all(self, batch_size: int = 200) -> dict[str, int]:
        """
        Sync all albums that have a Discogs ID.

        Returns summary counts:
        - total_checked
        - synced
        - skipped
        - failed
        """
        offset = 0
        total_checked = 0
        synced = 0
        skipped = 0
        failed = 0

        while True:
            albums, total = await self.album_service.list_albums(limit=batch_size, offset=offset, sort_by="title")
            if not albums:
                break

            for album in albums:
                total_checked += 1
                if not album.discogs_id:
                    skipped += 1
                    continue
                try:
                    await self.sync_album(album.id, album.discogs_id)
                    synced += 1
                except Exception:
                    failed += 1

            offset += len(albums)
            if offset >= total:
                break

        return {
            "total_checked": total_checked,
            "synced": synced,
            "skipped": skipped,
            "failed": failed,
        }

    @staticmethod
    def _parse_duration_seconds(raw: str | None) -> int | None:
        if not raw:
            return None
        value = raw.strip()
        if not value:
            return None
        if value.isdigit():
            return int(value)

        parts = value.split(":")
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            minutes, seconds = int(parts[0]), int(parts[1])
            return minutes * 60 + seconds
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return None

    @staticmethod
    def _parse_discogs_position(raw: str | None, fallback_index: int) -> tuple[str, str]:
        if raw:
            value = raw.strip()
            alpha_numeric = re.match(r"^([A-Za-z]+)\s*([0-9]+)$", value)
            if alpha_numeric:
                return alpha_numeric.group(1).upper(), alpha_numeric.group(2)

            disc_side = re.match(r"^([0-9]+)\s*[-.]\s*([0-9]+)$", value)
            if disc_side:
                return disc_side.group(1), disc_side.group(2)

            plain_number = re.match(r"^([0-9]+)$", value)
            if plain_number:
                return "A", plain_number.group(1)

        return "A", str(fallback_index)

    def _normalize_discogs_tracklist(self, tracklist: list[dict]) -> list[dict]:
        normalized: list[dict] = []
        fallback_index = 1
        for item in tracklist:
            if not isinstance(item, dict):
                continue
            track_type = str(item.get("type_") or "").lower()
            if track_type and track_type != "track":
                continue

            title = str(item.get("title") or "").strip()
            if not title:
                continue

            side, position = self._parse_discogs_position(item.get("position"), fallback_index)
            normalized.append({
                "side": side,
                "position": position,
                "title": title,
                "duration": self._parse_duration_seconds(item.get("duration")),
            })
            fallback_index += 1
        return normalized

