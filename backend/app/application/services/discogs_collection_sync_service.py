"""
Service for syncing Discogs user collections into MyCousinVinyl.
"""

from datetime import datetime
from typing import Awaitable, Callable, Dict, Any, List, Optional, Tuple
from uuid import UUID

from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.discogs_oauth_client import DiscogsOAuthClient
from app.application.services.collection_import_service import CollectionImportService

RowProcessedCallback = Callable[[Any], Awaitable[None]]


class DiscogsCollectionSyncService:
    def __init__(
        self,
        uow: UnitOfWork,
        oauth_client: DiscogsOAuthClient,
        import_service: CollectionImportService,
        import_log_level: str = "INFO",
    ):
        self.uow = uow
        self._client = oauth_client
        self._import_service = import_service
        self._import_log_level = import_log_level

    async def sync_collection(self, user_id: UUID) -> Any:
        return await self.sync_collection_with_callback(user_id, None)

    async def sync_collection_with_callback(
        self,
        user_id: UUID,
        on_row_processed: RowProcessedCallback | None,
    ) -> Any:
        async with self.uow:
            token = await self.uow.discogs_user_token_repository.get_by_user(user_id)
            if not token:
                raise ValueError("Discogs account not connected")

        releases = await self._fetch_all_collection_items(
            token.discogs_username,
            token.access_token,
            token.access_secret,
        )
        fields = await self._fetch_collection_fields(
            token.discogs_username,
            token.access_token,
            token.access_secret,
        )
        rows = await self._build_import_rows(
            releases,
            token.discogs_username,
            token.access_token,
            token.access_secret,
            fields,
        )
        job = await self._import_service.import_discogs_rows(
            user_id=user_id,
            rows=rows,
            filename="discogs-api",
            options={"source": "discogs_api", "skip_counts_as_error": False, "incremental": True},
            on_row_processed=on_row_processed,
        )

        token.last_synced_at = datetime.utcnow()
        async with self.uow:
            await self.uow.discogs_user_token_repository.upsert(token)
            await self.uow.commit()

        return job

    async def _fetch_all_collection_items(
        self,
        username: str,
        access_token: str,
        access_secret: str | None,
    ) -> List[Dict[str, Any]]:
        releases: List[Dict[str, Any]] = []
        page = 1
        per_page = 100
        pages = 1
        while page <= pages:
            response = await self._client.get_collection_items(
                username=username,
                folder_id=0,
                page=page,
                per_page=per_page,
                access_token=access_token,
                access_secret=access_secret,
            )
            releases.extend(response.get("releases", []))
            pagination = response.get("pagination") or {}
            pages = pagination.get("pages") or page
            page += 1
        return releases

    async def _fetch_collection_fields(
        self,
        username: str,
        access_token: str,
        access_secret: str | None,
    ) -> Dict[int, str]:
        response = await self._client.get_collection_fields(
            username=username,
            access_token=access_token,
            access_secret=access_secret,
        )
        fields = response.get("fields") or []
        mapping: Dict[int, str] = {}
        for field in fields:
            field_id = field.get("id")
            name = field.get("name")
            if field_id is None or not name:
                continue
            mapping[int(field_id)] = str(name)
        return mapping

    async def _fetch_instance_conditions(
        self,
        username: str,
        folder_id: int,
        release_id: int,
        instance_id: Optional[int],
        access_token: str,
        access_secret: str | None,
        field_name_by_id: Dict[int, str],
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if not instance_id:
            return None, None, None
        try:
            instance = await self._client.get_collection_instance(
                username=username,
                folder_id=folder_id,
                release_id=release_id,
                instance_id=instance_id,
                access_token=access_token,
                access_secret=access_secret,
            )
        except Exception:
            return None, None
        notes = instance.get("notes") or []
        media_condition = None
        sleeve_condition = None
        collection_notes = None
        for note in notes:
            field_id = note.get("field_id")
            value = note.get("value")
            if field_id is None or value is None:
                continue
            name = field_name_by_id.get(int(field_id), str(field_id))
            if name == "Media Condition":
                media_condition = str(value)
            elif name == "Sleeve Condition":
                sleeve_condition = str(value)
            elif name == "Collection Notes":
                collection_notes = str(value)
        self._log_import_detail(
            "Fetched collection instance conditions",
            release_id=release_id,
            instance_id=instance_id,
            media_condition=media_condition,
            sleeve_condition=sleeve_condition,
            collection_notes=collection_notes,
            media_condition_found=bool(media_condition),
            sleeve_condition_found=bool(sleeve_condition),
            collection_notes_found=bool(collection_notes),
        )
        return media_condition, sleeve_condition, collection_notes

    async def _build_import_rows(
        self,
        releases: List[Dict[str, Any]],
        username: str,
        access_token: str,
        access_secret: str | None,
        field_name_by_id: Dict[int, str],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for release in releases:
            basic = release.get("basic_information") or {}
            release_id = basic.get("id") or release.get("id")
            if not release_id:
                continue
            instance_id = release.get("instance_id")
            artists = basic.get("artists") or []
            artist_names = ", ".join(
                [artist.get("name", "").strip() for artist in artists if artist.get("name")]
            )
            title = basic.get("title") or ""
            media_condition, sleeve_condition, collection_notes = await self._fetch_instance_conditions(
                username=username,
                folder_id=0,
                release_id=int(release_id),
                instance_id=int(instance_id) if instance_id is not None else None,
                access_token=access_token,
                access_secret=access_secret,
                field_name_by_id=field_name_by_id,
            )
            self._log_import_detail(
                "Prepared import row",
                release_id=release_id,
                artist=artist_names,
                title=title,
                instance_id=instance_id,
                media_condition=media_condition,
                sleeve_condition=sleeve_condition,
                collection_notes=collection_notes,
            )
            rows.append(
                {
                    "release_id": str(release_id),
                    "Artist": artist_names,
                    "Title": title,
                    "Collection Media Condition": media_condition or "",
                    "Collection Sleeve Condition": sleeve_condition or "",
                    "Collection Notes": collection_notes or "",
                }
            )
        return rows

    def _log_import_detail(self, message: str, **data: Any) -> None:
        if str(self._import_log_level).upper() != "VERBOSE":
            return
        import logging
        logging.getLogger(__name__).info("%s | %s", message, data)
