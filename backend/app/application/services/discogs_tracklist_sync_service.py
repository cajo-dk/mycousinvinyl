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

    async def sync_album(
        self,
        album_id: UUID,
        discogs_id: Optional[int],
        preferred_release_id: Optional[int] = None,
    ) -> int:
        """Sync a single album tracklist from Discogs and return imported track count."""
        if not discogs_id and not preferred_release_id:
            raise ValueError("Album must have a Discogs ID before syncing tracks")

        details_candidates: list[dict[str, Any]] = []
        if preferred_release_id:
            try:
                details_candidates.append(await self.discogs_service.get_album(preferred_release_id, "release"))
            except Exception:
                pass

        if discogs_id:
            try:
                details_candidates.append(await self.discogs_service.get_album(discogs_id, "master"))
            except Exception:
                pass
            try:
                details_candidates.append(await self.discogs_service.get_album(discogs_id, "release"))
            except Exception:
                pass

        if not details_candidates:
            raise ValueError("Discogs lookup failed for both master and release tracklists")

        tracks_to_store: list[dict] = []
        best_performer_count = -1
        for details in details_candidates:
            raw_tracklist = details.get("tracklist") if isinstance(details, dict) else None
            normalized = self._normalize_discogs_tracklist(raw_tracklist or [])
            if not normalized:
                continue
            performer_count = sum(1 for row in normalized if row.get("performers"))
            if performer_count > best_performer_count:
                best_performer_count = performer_count
                tracks_to_store = normalized

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
        used_positions: set[tuple[str, str]] = set()
        fallback_index = 1
        active_heading_index: int | None = None
        for item in tracklist:
            if not isinstance(item, dict):
                continue
            track_type = str(item.get("type_") or "").lower()
            title = str(item.get("title") or "").strip()
            if not title:
                continue

            layout_type = "track"
            if track_type in {"heading", "index"}:
                layout_type = "heading"
            elif track_type and track_type != "track":
                continue

            side, position = self._parse_discogs_position(item.get("position"), fallback_index)
            side, position = self._reserve_unique_position(side, position, fallback_index, used_positions)
            normalized.append({
                "side": side,
                "position": position,
                "title": title,
                "duration": self._parse_duration_seconds(item.get("duration")),
                "layout_type": layout_type,
                "performers": self._parse_track_artists(item),
                "parent_index": active_heading_index if layout_type == "track" else None,
            })
            node_index = len(normalized) - 1
            fallback_index += 1

            if layout_type == "heading":
                active_heading_index = node_index
                continue

            sub_tracks = item.get("sub_tracks")
            if not isinstance(sub_tracks, list):
                continue

            subtrack_index = 1
            for sub in sub_tracks:
                if not isinstance(sub, dict):
                    continue
                sub_title = str(sub.get("title") or "").strip()
                if not sub_title:
                    continue

                sub_raw_position = sub.get("position")
                if sub_raw_position:
                    sub_side, sub_position = self._parse_discogs_position(sub_raw_position, fallback_index)
                else:
                    sub_side, sub_position = side, f"{position}.{subtrack_index}"

                sub_side, sub_position = self._reserve_unique_position(
                    sub_side,
                    sub_position,
                    fallback_index,
                    used_positions,
                )
                normalized.append({
                    "side": sub_side,
                    "position": sub_position,
                    "title": sub_title,
                    "duration": self._parse_duration_seconds(sub.get("duration")),
                    "layout_type": "subtrack",
                    "performers": self._parse_track_artists(sub) or self._parse_track_artists(item),
                    "parent_index": node_index,
                })
                subtrack_index += 1
                fallback_index += 1
        return normalized

    @staticmethod
    def _parse_track_artists(item: dict[str, Any]) -> list[str]:
        artists = item.get("artists")
        if not isinstance(artists, list):
            return []

        values: list[str] = []
        seen: set[str] = set()
        for artist in artists:
            raw_name = ""
            if isinstance(artist, dict):
                raw_name = str(artist.get("name") or artist.get("anv") or "").strip()
            elif isinstance(artist, str):
                raw_name = artist.strip()
            if not raw_name:
                continue
            clean_name = re.sub(r"\s\(\d+\)$", "", raw_name).strip()
            key = clean_name.lower()
            if key in seen:
                continue
            seen.add(key)
            values.append(clean_name)
        return values

    @staticmethod
    def _reserve_unique_position(
        side: str,
        position: str,
        fallback_index: int,
        used_positions: set[tuple[str, str]],
    ) -> tuple[str, str]:
        normalized_side = (side or "A").strip().upper()[:10] or "A"
        normalized_position = (position or str(fallback_index)).strip()[:10] or str(fallback_index)

        candidate = (normalized_side, normalized_position)
        if candidate not in used_positions:
            used_positions.add(candidate)
            return candidate

        suffix = 2
        while True:
            base = normalized_position[: max(1, 10 - len(str(suffix)) - 1)]
            candidate = (normalized_side, f"{base}.{suffix}")
            if candidate not in used_positions:
                used_positions.add(candidate)
                return candidate
            suffix += 1

