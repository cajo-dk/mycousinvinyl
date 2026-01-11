"""
Collection import service for Discogs CSV exports.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.application.ports.unit_of_work import UnitOfWork
from app.application.services.discogs_service import DiscogsService
from app.domain.entities import (
    Artist,
    Album,
    Pressing,
    CollectionItem,
    CollectionImport,
    CollectionImportRow,
    SystemLogEntry,
)
from app.domain.value_objects import (
    ArtistType,
    Condition,
    DataSource,
    ReleaseType,
    VinylFormat,
    VinylSize,
    VinylSpeed,
    EditionType,
)

logger = logging.getLogger(__name__)

RowProcessedCallback = Callable[[CollectionImportRow], Awaitable[None]]


class ImportSkip(Exception):
    """Raised when a row should be skipped without failing the entire import."""


class CollectionImportService:
    """Service for importing external collection exports."""

    def __init__(self, uow: UnitOfWork, discogs_service: DiscogsService, import_log_level: str = "INFO"):
        self.uow = uow
        self.discogs_service = discogs_service
        self._country_code_cache: Optional[Dict[str, str]] = None
        self._genre_id_cache: Optional[Dict[str, UUID]] = None
        self._style_id_cache: Optional[Dict[str, UUID]] = None
        self._import_log_level = import_log_level

    async def import_discogs_csv(
        self,
        user_id: UUID,
        filename: str,
        content: bytes,
        on_row_processed: Optional["RowProcessedCallback"] = None,
    ) -> CollectionImport:
        rows = self._parse_csv(content)
        started_at = datetime.utcnow()
        import_job = CollectionImport(
            user_id=user_id,
            filename=filename,
            status="processing",
            total_rows=len(rows),
            processed_rows=0,
            success_count=0,
            error_count=0,
            started_at=started_at,
            options={"source": "discogs_csv", "skip_counts_as_error": True},
        )

        async with self.uow:
            import_job = await self.uow.collection_import_repository.create_import(import_job)
            row_entities = [
                CollectionImportRow(
                    import_id=import_job.id,
                    row_number=index,
                    status="pending",
                    raw_data=row,
                    discogs_release_id=self._parse_int(row.get("release_id")),
                )
                for index, row in enumerate(rows, start=1)
            ]
            if row_entities:
                await self.uow.collection_import_repository.add_rows(row_entities)
            await self.uow.collection_import_repository.update_import(import_job)
            await self.uow.commit()

        for row in row_entities:
            await self._process_row(import_job.id, user_id, row, on_row_processed)

        ok_count = sum(1 for row in row_entities if row.status == "success")
        skipped_count = sum(1 for row in row_entities if row.status == "skipped")
        failed_count = sum(1 for row in row_entities if row.status == "error")

        async with self.uow:
            import_job = await self.uow.collection_import_repository.get_import(import_job.id, user_id)
            if import_job:
                import_job.status = "completed"
                import_job.completed_at = datetime.utcnow()
                await self.uow.collection_import_repository.update_import(import_job)
                await self.uow.system_log_repository.create(SystemLogEntry(
                    user_id=None,
                    user_name="*system",
                    severity="INFO",
                    component="Import",
                    message=(
                        "Discogs import completed for "
                        f"{await self._resolve_user_label(user_id)}: "
                        f"OK {ok_count}, "
                        f"Skipped {skipped_count}, "
                        f"Failed {failed_count}"
                    ),
                ))
                await self.uow.commit()
            return import_job

    async def import_discogs_rows(
        self,
        user_id: UUID,
        rows: List[Dict[str, Any]],
        filename: str = "discogs-api",
        options: Optional[Dict[str, Any]] = None,
        on_row_processed: Optional["RowProcessedCallback"] = None,
    ) -> CollectionImport:
        started_at = datetime.utcnow()
        import_job = CollectionImport(
            user_id=user_id,
            filename=filename,
            status="processing",
            total_rows=len(rows),
            processed_rows=0,
            success_count=0,
            error_count=0,
            started_at=started_at,
            options=options or {"source": "discogs_api", "skip_counts_as_error": False},
        )

        async with self.uow:
            import_job = await self.uow.collection_import_repository.create_import(import_job)
            row_entities = [
                CollectionImportRow(
                    import_id=import_job.id,
                    row_number=index,
                    status="pending",
                    raw_data=row,
                    discogs_release_id=self._parse_int(row.get("release_id")),
                )
                for index, row in enumerate(rows, start=1)
            ]
            if row_entities:
                await self.uow.collection_import_repository.add_rows(row_entities)
            await self.uow.collection_import_repository.update_import(import_job)
            await self.uow.commit()

        for row in row_entities:
            await self._process_row(import_job.id, user_id, row, on_row_processed)

        ok_count = sum(1 for row in row_entities if row.status == "success")
        skipped_count = sum(1 for row in row_entities if row.status == "skipped")
        failed_count = sum(1 for row in row_entities if row.status == "error")

        async with self.uow:
            import_job = await self.uow.collection_import_repository.get_import(import_job.id, user_id)
            if import_job:
                import_job.status = "completed"
                import_job.completed_at = datetime.utcnow()
                await self.uow.collection_import_repository.update_import(import_job)
                await self.uow.system_log_repository.create(SystemLogEntry(
                    user_id=None,
                    user_name="*system",
                    severity="INFO",
                    component="Import",
                    message=(
                        "Discogs import completed for "
                        f"{await self._resolve_user_label(user_id)}: "
                        f"OK {ok_count}, "
                        f"Skipped {skipped_count}, "
                        f"Failed {failed_count}"
                    ),
                ))
                await self.uow.commit()
            return import_job

    async def get_import(self, import_id: UUID, user_id: UUID) -> Optional[CollectionImport]:
        async with self.uow:
            return await self.uow.collection_import_repository.get_import(import_id, user_id)

    async def get_import_rows(
        self,
        import_id: UUID,
        user_id: UUID,
        limit: int = 500,
    ) -> List[CollectionImportRow]:
        async with self.uow:
            return await self.uow.collection_import_repository.get_rows(import_id, user_id, limit)

    async def _process_row(
        self,
        import_id: UUID,
        user_id: UUID,
        row: CollectionImportRow,
        on_row_processed: Optional["RowProcessedCallback"] = None,
    ) -> None:
        async with self.uow:
            import_job = await self.uow.collection_import_repository.get_import(import_id, user_id)
            if not import_job:
                return

            try:
                await self._apply_row(user_id, row)
                row.status = "success"
                import_job.success_count += 1
            except ImportSkip as exc:
                row.status = "skipped"
                row.error_message = str(exc)
                if import_job.options.get("skip_counts_as_error", True):
                    import_job.error_count += 1
            except Exception as exc:
                logger.exception("Import row %s failed", row.row_number)
                row.status = "error"
                row.error_message = str(exc)
                import_job.error_count += 1
            finally:
                await self._log_row_result(user_id, row)
                import_job.processed_rows += 1
                await self.uow.collection_import_repository.update_row(row)
                await self.uow.collection_import_repository.update_import(import_job)
                await self.uow.commit()
                if on_row_processed:
                    await on_row_processed(row)

    async def _apply_row(self, user_id: UUID, row: CollectionImportRow) -> None:
        raw = row.raw_data
        release_id = self._parse_int(raw.get("release_id"))
        if not release_id:
            raise ImportSkip("Missing Discogs release_id")

        release = await self.discogs_service.get_release(release_id)
        format_value, speed, size = self._resolve_format(raw, release)

        artist_name = (raw.get("Artist") or "").strip()
        if not artist_name:
            raise ImportSkip("Missing artist name")

        album_title = (raw.get("Title") or "").strip()
        if not album_title:
            raise ImportSkip("Missing album title")

        release_type = self._resolve_release_type(raw, release)
        release_year_raw = self._parse_year(raw.get("Released"))
        release_year = release_year_raw or release.get("year")
        catalog_number_raw = (raw.get("Catalog#") or "").strip()
        catalog_number = catalog_number_raw or release.get("catalog_number")
        label_raw = (raw.get("Label") or "").strip()
        label = label_raw or release.get("label")
        album_discogs_id = release.get("master_id") or release_id
        genre_ids = await self._resolve_genre_ids(release.get("genres") or [])
        style_ids = await self._resolve_style_ids(release.get("styles") or [])

        artist = await self.uow.artist_repository.get_by_name(artist_name)
        artist_created = False
        if not artist:
            artist_details = await self._lookup_artist_details(artist_name)
            artist_type = self._resolve_artist_type(artist_details.get("artist_type"))
            artist_country = await self._normalize_country_code(artist_details.get("country"))
            artist = Artist(
                name=artist_details.get("name") or artist_name,
                sort_name=artist_details.get("sort_name") or "",
                country=artist_country,
                bio=artist_details.get("bio"),
                image_url=artist_details.get("image_url"),
                begin_date=artist_details.get("begin_date"),
                end_date=artist_details.get("end_date"),
                discogs_id=artist_details.get("id"),
                type=artist_type,
                created_by=user_id,
                data_source=DataSource.IMPORT,
            )
            artist = await self.uow.artist_repository.add(artist)
            artist_created = True
            entry = SystemLogEntry(
                user_id=None,
                user_name="*system",
                severity="INFO",
                component="Import",
                message=f"Discogs import created artist for {await self._resolve_user_label(user_id)}: {artist.name}",
            )
            await self.uow.system_log_repository.create(entry)

        album = await self.uow.album_repository.get_by_discogs_id(album_discogs_id)
        album_created = False
        if not album:
            album_country = await self._normalize_country_code(release.get("country"))
            album = Album(
                title=album_title,
                primary_artist_id=artist.id,
                release_type=release_type,
                original_release_year=release_year,
                country_of_origin=album_country,
                label=label,
                catalog_number_base=catalog_number,
                image_url=release.get("image_url"),
                discogs_id=album_discogs_id,
                genre_ids=genre_ids,
                style_ids=style_ids,
                created_by=user_id,
                data_source=DataSource.IMPORT,
            )
            album = await self.uow.album_repository.add(album)
            album_created = True
        else:
            if (genre_ids and not album.genre_ids) or (style_ids and not album.style_ids):
                if genre_ids and not album.genre_ids:
                    album.genre_ids = genre_ids
                if style_ids and not album.style_ids:
                    album.style_ids = style_ids
                album = await self.uow.album_repository.update(album)

        pressing = await self.uow.pressing_repository.get_by_discogs_release_id(release_id)
        pressing_created = False
        if not pressing:
            edition_type = self._resolve_edition_type(release.get("edition_type"))
            pressing_country = await self._normalize_country_code(release.get("country"))
            pressing = Pressing(
                album_id=album.id,
                format=format_value,
                speed_rpm=speed,
                size_inches=size,
                disc_count=release.get("disc_count") or 1,
                pressing_country=pressing_country,
                pressing_year=release.get("year") or release_year,
                pressing_plant=release.get("pressing_plant"),
                mastering_engineer=release.get("mastering_engineer"),
                mastering_studio=release.get("mastering_studio"),
                vinyl_color=release.get("vinyl_color"),
                edition_type=edition_type,
                image_url=release.get("image_url"),
                discogs_release_id=release_id,
                discogs_master_id=release.get("master_id"),
                master_title=release.get("master_title"),
                created_by=user_id,
                data_source=DataSource.IMPORT,
            )
            pressing = await self.uow.pressing_repository.add(pressing)
            pressing_created = True

        already_owned = await self.uow.collection_repository.exists_for_user_pressing(user_id, pressing.id)
        if already_owned:
            raise ImportSkip("User already owns this pressing")

        media_condition_raw = raw.get("Collection Media Condition")
        sleeve_condition_raw = raw.get("Collection Sleeve Condition")
        media_condition = self._resolve_condition(media_condition_raw)
        sleeve_condition = self._resolve_condition(sleeve_condition_raw)
        rating = self._parse_int(raw.get("Rating"))
        date_added = self._parse_datetime(raw.get("Date Added"))

        collection_item = CollectionItem(
            user_id=user_id,
            pressing_id=pressing.id,
            media_condition=media_condition,
            sleeve_condition=sleeve_condition,
            user_rating=rating,
            user_notes=(raw.get("Collection Notes") or "").strip() or None,
            storage_location=(raw.get("CollectionFolder") or "").strip() or None,
            date_added=date_added or datetime.utcnow(),
        )
        collection_item = await self.uow.collection_repository.add(collection_item)

        row.artist_id = artist.id
        row.album_id = album.id
        row.pressing_id = pressing.id
        row.collection_item_id = collection_item.id

        self._log_import_detail(
            "Imported collection row",
            release_id=release_id,
            artist=artist_name,
            title=album_title,
            format=format_value.value if hasattr(format_value, "value") else str(format_value),
            speed_rpm=speed.value if hasattr(speed, "value") else str(speed),
            size_inches=size.value if hasattr(size, "value") else str(size),
            release_type=release_type.value if hasattr(release_type, "value") else str(release_type),
            release_year=release_year,
            release_year_source=self._resolve_source(release_year_raw, release.get("year")),
            label=label,
            label_source=self._resolve_source(label_raw, release.get("label")),
            catalog_number=catalog_number,
            catalog_number_source=self._resolve_source(catalog_number_raw, release.get("catalog_number")),
            media_condition=media_condition.value,
            media_condition_source="raw" if media_condition_raw else "default",
            sleeve_condition=sleeve_condition.value,
            sleeve_condition_source="raw" if sleeve_condition_raw else "default",
            artist_created=artist_created,
            album_created=album_created,
            pressing_created=pressing_created,
            collection_item_created=True,
        )

    def _resolve_source(self, raw_value: Optional[str], fallback_value: Optional[str]) -> str:
        if raw_value:
            return "raw"
        if fallback_value:
            return "release"
        return "default"

    def _log_import_detail(self, message: str, **data: Any) -> None:
        if str(self._import_log_level).upper() != "VERBOSE":
            return
        logger.info("%s | %s", message, data)

    async def _log_row_result(self, user_id: UUID, row: CollectionImportRow) -> None:
        raw = row.raw_data or {}
        artist = (raw.get("Artist") or "").strip() or "Unknown Artist"
        title = (raw.get("Title") or "").strip() or "Unknown Album"
        user_label = await self._resolve_user_label(user_id)
        if row.status == "success":
            severity = "INFO"
            message = f"Discogs import for {user_label}: {artist} - {title}"
        elif row.status == "skipped":
            severity = "WARN"
            reason = row.error_message or "skipped"
            message = f"Discogs import skipped for {user_label}: {artist} - {title} ({reason})"
        else:
            severity = "ERROR"
            error_text = row.error_message or row.status
            message = f"Discogs import failed for {user_label}: {artist} - {title} ({error_text})"

        entry = SystemLogEntry(
            user_id=None,
            user_name="*system",
            severity=severity,
            component="Import",
            message=message,
        )
        await self.uow.system_log_repository.create(entry)

    async def _resolve_user_label(self, user_id: UUID) -> str:
        prefs = await self.uow.preferences_repository.get_or_create_default(user_id)
        profile = prefs.get_user_profile()
        display_name = profile.get("display_name")
        if display_name:
            return display_name
        return str(user_id)

    async def _lookup_artist_details(self, artist_name: str) -> Dict[str, Any]:
        try:
            results = await self.discogs_service.search_artists(artist_name, limit=5)
        except Exception:
            logger.exception("Discogs artist search failed for %s", artist_name)
            return {}

        if not results:
            return {}

        normalized = self._normalize_artist_name(artist_name)
        best_match = None
        for candidate in results:
            candidate_name = self._normalize_artist_name(candidate.get("name") or "")
            if candidate_name == normalized:
                best_match = candidate
                break

        if not best_match:
            best_match = results[0]

        artist_id = best_match.get("id")
        if not artist_id:
            return {}

        try:
            return await self.discogs_service.get_artist(artist_id)
        except Exception:
            logger.exception("Discogs artist lookup failed for %s", artist_id)
            return {}

    def _normalize_artist_name(self, name: str) -> str:
        text = name.strip().lower()
        if text.endswith(")") and "(" in text:
            prefix, suffix = text.rsplit("(", 1)
            if suffix.strip(") ").isdigit():
                text = prefix.strip()
        return text

    def _resolve_artist_type(self, value: Optional[str]) -> ArtistType:
        if not value:
            return ArtistType.PERSON
        lowered = str(value).strip().lower()
        if "group" in lowered or "band" in lowered or "collective" in lowered:
            return ArtistType.GROUP
        return ArtistType.PERSON

    async def _resolve_genre_ids(self, values: List[str]) -> List[UUID]:
        if not values:
            return []
        cache = await self._get_genre_cache()
        resolved: List[UUID] = []
        for raw in values:
            name = str(raw).strip()
            if not name:
                continue
            key = name.lower()
            existing = cache.get(key)
            if existing:
                resolved.append(existing)
                continue
            try:
                created = await self.uow.lookup_repository.create_genre(name)
            except IntegrityError:
                await self.uow.rollback()
                cache = await self._refresh_genre_cache()
                existing = cache.get(key)
                if existing:
                    resolved.append(existing)
                continue
            cache[key] = created.id
            resolved.append(created.id)
        return resolved

    async def _resolve_style_ids(self, values: List[str]) -> List[UUID]:
        if not values:
            return []
        cache = await self._get_style_cache()
        resolved: List[UUID] = []
        for raw in values:
            name = str(raw).strip()
            if not name:
                continue
            key = name.lower()
            existing = cache.get(key)
            if existing:
                resolved.append(existing)
                continue
            try:
                created = await self.uow.lookup_repository.create_style(name)
            except IntegrityError:
                await self.uow.rollback()
                cache = await self._refresh_style_cache()
                existing = cache.get(key)
                if existing:
                    resolved.append(existing)
                continue
            cache[key] = created.id
            resolved.append(created.id)
        return resolved

    async def _get_genre_cache(self) -> Dict[str, UUID]:
        if self._genre_id_cache is None:
            self._genre_id_cache = await self._refresh_genre_cache()
        return self._genre_id_cache

    async def _refresh_genre_cache(self) -> Dict[str, UUID]:
        genres = await self.uow.lookup_repository.get_all_genres()
        return {genre.name.strip().lower(): genre.id for genre in genres if genre.name}

    async def _get_style_cache(self) -> Dict[str, UUID]:
        if self._style_id_cache is None:
            self._style_id_cache = await self._refresh_style_cache()
        return self._style_id_cache

    async def _refresh_style_cache(self) -> Dict[str, UUID]:
        styles = await self.uow.lookup_repository.get_all_styles()
        return {style.name.strip().lower(): style.id for style in styles if style.name}

    async def _normalize_country_code(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        text = str(value).strip()
        if not text:
            return None
        if len(text) == 2:
            return text.upper()

        lookup = await self._get_country_code_map()
        lowered = text.lower()
        return lookup.get(lowered)

    async def _get_country_code_map(self) -> Dict[str, str]:
        if self._country_code_cache is not None:
            return self._country_code_cache

        countries = await self.uow.lookup_repository.get_all_countries()
        lookup: Dict[str, str] = {}
        for country in countries:
            if country.name:
                lookup[country.name.strip().lower()] = country.code.upper()
            lookup[country.code.strip().lower()] = country.code.upper()

        aliases = {
            "usa": "US",
            "u.s.a.": "US",
            "u.s.": "US",
            "united states of america": "US",
            "uk": "GB",
            "u.k.": "GB",
            "england": "GB",
            "scotland": "GB",
            "wales": "GB",
        }
        lookup.update(aliases)

        self._country_code_cache = lookup
        return lookup

    def _parse_csv(self, content: bytes) -> List[Dict[str, Any]]:
        text = content.decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(text))
        rows: List[Dict[str, Any]] = []
        for row in reader:
            rows.append({key.strip(): (value or "").strip() for key, value in row.items()})
        return rows

    def _resolve_format(
        self,
        raw: Dict[str, Any],
        release: Dict[str, Any],
    ) -> Tuple[VinylFormat, VinylSpeed, VinylSize]:
        tokens = self._collect_format_tokens(raw, release)
        if any("cassette" in token or "dvd" in token for token in tokens):
            raise ImportSkip("Unsupported format: non-vinyl")

        format_value = None
        if any("cd" in token for token in tokens):
            format_value = VinylFormat.CD
        elif any("lp" in token for token in tokens):
            format_value = VinylFormat.LP
        elif any(token == "ep" or "ep" in token for token in tokens):
            format_value = VinylFormat.EP
        elif any("single" in token for token in tokens):
            format_value = VinylFormat.SINGLE
        elif any("maxi" in token for token in tokens):
            format_value = VinylFormat.MAXI
        elif any("vinyl" in token for token in tokens):
            format_value = VinylFormat.LP

        if not format_value:
            raise ImportSkip("Unsupported format: missing vinyl format")

        size = self._resolve_size(tokens, format_value)
        speed = self._resolve_speed(tokens, format_value)
        return format_value, speed, size

    def _resolve_size(self, tokens: List[str], format_value: VinylFormat) -> VinylSize:
        if format_value == VinylFormat.CD:
            return VinylSize.CD
        if any('7"' in token or '7 inch' in token for token in tokens):
            return VinylSize.SIZE_7
        if any('10"' in token or '10 inch' in token for token in tokens):
            return VinylSize.SIZE_10
        if any('12"' in token or '12 inch' in token for token in tokens):
            return VinylSize.SIZE_12
        if format_value == VinylFormat.SINGLE:
            return VinylSize.SIZE_7
        return VinylSize.SIZE_12

    def _resolve_speed(self, tokens: List[str], format_value: VinylFormat) -> VinylSpeed:
        if format_value == VinylFormat.CD:
            return VinylSpeed.NA
        if any("78" in token for token in tokens):
            return VinylSpeed.RPM_78
        if any("45" in token for token in tokens):
            return VinylSpeed.RPM_45
        if format_value == VinylFormat.SINGLE:
            return VinylSpeed.RPM_45
        return VinylSpeed.RPM_33

    def _resolve_release_type(self, raw: Dict[str, Any], release: Dict[str, Any]) -> ReleaseType:
        tokens = self._collect_format_tokens(raw, release)
        if any("compilation" in token for token in tokens):
            return ReleaseType.COMPILATION
        if any("live" in token for token in tokens):
            return ReleaseType.LIVE
        if any(token == "ep" or "ep" in token for token in tokens):
            return ReleaseType.EP
        if any("single" in token for token in tokens):
            return ReleaseType.SINGLE
        if any("box" in token for token in tokens):
            return ReleaseType.BOX_SET
        return ReleaseType.STUDIO

    def _collect_format_tokens(self, raw: Dict[str, Any], release: Dict[str, Any]) -> List[str]:
        tokens: List[str] = []
        raw_format = raw.get("Format") or ""
        tokens.extend([part.strip().lower() for part in raw_format.split(",") if part.strip()])
        for item in release.get("formats") or []:
            tokens.append(str(item).strip().lower())
        for item in release.get("format_descriptions") or []:
            tokens.append(str(item).strip().lower())
        return tokens

    def _resolve_condition(self, value: Optional[str]) -> Condition:
        if not value:
            return Condition.VG_PLUS
        lowered = value.strip().lower()
        mapping = {
            "mint": Condition.MINT,
            "mint (m)": Condition.MINT,
            "near mint": Condition.NEAR_MINT,
            "near mint (nm or m-)": Condition.NEAR_MINT,
            "near mint (nm)": Condition.NEAR_MINT,
            "nm": Condition.NEAR_MINT,
            "nm or m-": Condition.NEAR_MINT,
            "very good plus": Condition.VG_PLUS,
            "very good plus (vg+)": Condition.VG_PLUS,
            "vg+": Condition.VG_PLUS,
            "very good": Condition.VG,
            "very good (vg)": Condition.VG,
            "vg": Condition.VG,
            "good plus": Condition.GOOD,
            "good plus (g+)": Condition.GOOD,
            "g+": Condition.GOOD,
            "good": Condition.GOOD,
            "good (g)": Condition.GOOD,
            "g": Condition.GOOD,
            "poor": Condition.POOR,
            "poor (p)": Condition.POOR,
            "p": Condition.POOR,
            "fair": Condition.POOR,
            "fair (f)": Condition.POOR,
            "f": Condition.POOR,
        }
        if lowered in mapping:
            return mapping[lowered]
        if "near mint" in lowered:
            return Condition.NEAR_MINT
        if "vg+" in lowered:
            return Condition.VG_PLUS
        if "vg" in lowered:
            return Condition.VG
        if "good" in lowered:
            return Condition.GOOD
        if "mint" in lowered:
            return Condition.MINT
        return Condition.VG_PLUS

    def _resolve_edition_type(self, value: Optional[str]) -> str:
        if not value:
            return EditionType.STANDARD
        lowered = str(value).strip().lower()
        if "limited" in lowered:
            return EditionType.LIMITED
        if "numbered" in lowered:
            return EditionType.NUMBERED
        if "reissue" in lowered:
            return EditionType.REISSUE
        if "remaster" in lowered:
            return EditionType.REMASTER
        return EditionType.STANDARD

    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        try:
            return int(cleaned)
        except ValueError:
            return None

    def _parse_year(self, value: Optional[str]) -> Optional[int]:
        parsed = self._parse_int(value)
        if parsed and parsed > 0:
            return parsed
        return None

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        text = value.strip()
        if not text:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None
