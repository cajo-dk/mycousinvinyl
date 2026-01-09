"""
Collection API endpoints.

CRITICAL SECURITY: All operations are user-scoped.
User ID is extracted from authenticated context, never from request body.
"""

from typing import Annotated, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
import asyncio
import json

from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.authorization import require_viewer, require_editor
from app.entrypoints.http.dependencies import (
    get_collection_service,
    get_collection_import_service,
    get_discogs_collection_sync_service,
)
from app.entrypoints.http.schemas.collection import (
    CollectionItemCreate, CollectionItemUpdate, CollectionItemResponse,
    ConditionUpdateRequest, PurchaseInfoUpdateRequest, RatingUpdateRequest,
    CollectionSearchParams, CollectionStatistics, CollectionItemDetailResponse,
    ArtistSummary, AlbumSummary, MarketDataSummary,
    AlbumPlayIncrementResponse, PlayedAlbumEntry
)
from app.entrypoints.http.schemas.collection_import import (
    CollectionImportResponse,
    CollectionImportRowResponse,
)
from app.entrypoints.http.schemas.common import PaginatedResponse, MessageResponse
from app.application.services.collection_service import CollectionService
from app.application.services.collection_import_service import CollectionImportService
from app.application.services.discogs_collection_sync_service import DiscogsCollectionSyncService
from app.domain.value_objects import Condition


router = APIRouter(prefix="/collection", tags=["Collection"])


def _build_import_response(
    job,
    rows,
) -> CollectionImportResponse:
    response_rows = []
    for row in rows:
        raw = row.raw_data or {}
        result = "success" if row.status == "success" else "fail"
        message = "OK" if row.status == "success" else (row.error_message or "Failed")
        response_rows.append(
            CollectionImportRowResponse(
                row_number=row.row_number,
                result=result,
                message=message,
                discogs_release_id=row.discogs_release_id,
                artist=(raw.get("Artist") or "").strip() or None,
                title=(raw.get("Title") or "").strip() or None,
            )
        )
    return CollectionImportResponse(
        id=job.id,
        filename=job.filename,
        status=job.status,
        total_rows=job.total_rows,
        processed_rows=job.processed_rows,
        success_count=job.success_count,
        error_count=job.error_count,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_summary=job.error_summary,
        rows=response_rows,
    )


@router.post(
    "/imports/discogs",
    response_model=CollectionImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import collection from Discogs CSV",
    dependencies=[Depends(require_editor())]
)
async def import_discogs_collection(
    service: Annotated[CollectionImportService, Depends(get_collection_import_service)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
):
    """
    Import a Discogs CSV export into the user's collection.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is required")
    content = await file.read()
    try:
        job = await service.import_discogs_csv(user.sub, file.filename, content)
        rows = await service.get_import_rows(job.id, user.sub)
        return _build_import_response(job, rows)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/imports/discogs/sync",
    response_model=CollectionImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sync collection from Discogs API",
    dependencies=[Depends(require_editor())],
)
async def sync_discogs_collection(
    sync_service: Annotated[DiscogsCollectionSyncService, Depends(get_discogs_collection_sync_service)],
    import_service: Annotated[CollectionImportService, Depends(get_collection_import_service)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Sync Discogs collection items using the Discogs API (OAuth).
    """
    try:
        job = await sync_service.sync_collection(user.sub)
        rows = await import_service.get_import_rows(job.id, user.sub)
        return _build_import_response(job, rows)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/imports/discogs/sync/stream",
    summary="Stream Discogs API sync status",
    dependencies=[Depends(require_editor())],
)
async def stream_discogs_collection_sync(
    sync_service: Annotated[DiscogsCollectionSyncService, Depends(get_discogs_collection_sync_service)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Stream Discogs collection sync status updates as Server-Sent Events (SSE).
    """

    async def event_generator():
        queue: asyncio.Queue[dict] = asyncio.Queue()
        done = asyncio.Event()

        async def on_row_processed(row):
            raw = row.raw_data or {}
            artist = (raw.get("Artist") or "").strip()
            title = (raw.get("Title") or "").strip()
            if row.status == "success":
                result = "OK"
            elif row.status == "skipped":
                result = row.error_message or "Skipped"
            else:
                result = row.error_message or "Failed"
            await queue.put({
                "type": "row",
                "artist": artist or None,
                "title": title or None,
                "result": result,
            })

        async def run_sync():
            try:
                job = await sync_service.sync_collection_with_callback(user.sub, on_row_processed)
                await queue.put({"type": "complete", "import_id": str(job.id)})
            except Exception as exc:
                await queue.put({"type": "error", "message": str(exc)})
            finally:
                done.set()

        asyncio.create_task(run_sync())

        while True:
            if done.is_set() and queue.empty():
                break
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=10)
                yield f"data: {json.dumps(payload)}\n\n"
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get(
    "/imports/{import_id}",
    response_model=CollectionImportResponse,
    summary="Get collection import status",
    dependencies=[Depends(require_viewer())]
)
async def get_collection_import(
    import_id: UUID,
    service: Annotated[CollectionImportService, Depends(get_collection_import_service)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Get status for a collection import job.
    """
    job = await service.get_import(import_id, user.sub)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job {import_id} not found or access denied"
        )
    rows = await service.get_import_rows(job.id, user.sub)
    return _build_import_response(job, rows)


@router.post(
    "",
    response_model=CollectionItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add pressing to collection",
    dependencies=[Depends(require_editor())]
)
async def add_to_collection(
    item_data: CollectionItemCreate,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Add a pressing to your collection.

    User ID extracted from authenticated token.
    """
    try:
        item = await service.add_to_collection(
            user_id=user.sub,  # SECURITY: Extract from auth context
            user_name=user.name,
            user_email=user.email,
            pressing_id=item_data.pressing_id,
            media_condition=item_data.media_condition,
            sleeve_condition=item_data.sleeve_condition,
            purchase_price=item_data.purchase_price,
            purchase_currency=item_data.purchase_currency,
            purchase_date=item_data.purchase_date,
            seller=item_data.seller,
            storage_location=item_data.location,
            defect_notes=item_data.defect_notes,
            notes=item_data.notes
        )
        return item
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/with-details",
    response_model=PaginatedResponse[CollectionItemDetailResponse],
    summary="Get collection with artist and album details",
    dependencies=[Depends(require_viewer())]
)
async def get_collection_with_details(
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)],
    query: str = Query(None, min_length=1, description="Search albums and artists"),
    sort_by: str = Query("artist_album", description="Sort: artist_album, date_added_desc, date_added_asc"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get your collection with enriched artist and album details.

    Returns collection items with joined artist/album data for hierarchical display.
    Ordered alphabetically by artist (sort_name), then album year, then album title.
    """
    items_data, total = await service.get_collection_with_details(
        user_id=user.sub,
        query=query,
        limit=limit,
        offset=offset,
        sort_by=sort_by
    )

    # Transform data into response schema
    response_items = []
    for item_data in items_data:
        collection_item = item_data["collection_item"]
        pressing = item_data["pressing"]
        artist = item_data["artist"]
        album = item_data["album"]
        genres = item_data["genres"]
        market_data = item_data.get("market_data")

        # Map market_data to MarketDataSummary if it exists
        market_data_summary = None
        if market_data:
            market_data_summary = MarketDataSummary(
                min_value=market_data.min_value,
                median_value=market_data.median_value,
                max_value=market_data.max_value,
                currency=market_data.currency,
                updated_at=market_data.updated_at
            )

        response_items.append(
            CollectionItemDetailResponse(
                id=collection_item.id,
                user_id=collection_item.user_id,
                pressing_id=collection_item.pressing_id,
                pressing_image_url=pressing.image_url,
                media_condition=collection_item.media_condition,
                sleeve_condition=collection_item.sleeve_condition,
                purchase_price=collection_item.purchase_price,
                purchase_currency=collection_item.purchase_currency,
                purchase_date=collection_item.purchase_date,
                seller=collection_item.seller,
                location=collection_item.storage_location,
                defect_notes=collection_item.defect_notes,
                notes=collection_item.user_notes,
                rating=collection_item.user_rating,
                play_count=collection_item.play_count,
                last_played=collection_item.last_played_date,
                date_added=collection_item.date_added,
                updated_at=collection_item.updated_at,
                artist=ArtistSummary(
                    id=artist.id,
                    name=artist.name,
                    sort_name=artist.sort_name,
                    country=artist.country
                ),
                album=AlbumSummary(
                    id=album.id,
                    title=album.title,
                    release_year=album.original_release_year,
                    genres=genres,
                    image_url=album.image_url
                ),
                market_data=market_data_summary
            )
        )

    return PaginatedResponse(
        items=response_items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/statistics",
    response_model=CollectionStatistics,
    summary="Get collection statistics",
    dependencies=[Depends(require_viewer())]
)
async def get_collection_statistics(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CollectionService, Depends(get_collection_service)]
):
    """
    Get statistics about your collection.

    Returns total count, purchase price totals, min/avg/max values.
    """
    stats = await service.get_collection_statistics(user.sub)
    return stats


@router.get(
    "/{item_id}",
    response_model=CollectionItemResponse,
    summary="Get collection item by ID",
    dependencies=[Depends(require_viewer())]
)
async def get_collection_item(
    item_id: UUID,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Get a specific item from your collection.

    SECURITY: Verifies user owns the item.
    """
    item = await service.get_collection_item(item_id, user.sub)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection item {item_id} not found or access denied"
        )
    return item


@router.get(
    "",
    response_model=PaginatedResponse[CollectionItemResponse],
    summary="Get your collection",
    dependencies=[Depends(require_viewer())]
)
async def get_collection(
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)],
    query: str = Query(None, min_length=1, description="Search albums and artists"),
    media_conditions: List[Condition] = Query(None, description="Filter by media conditions"),
    sleeve_conditions: List[Condition] = Query(None, description="Filter by sleeve conditions"),
    rating_min: int = Query(None, ge=0, le=5),
    rating_max: int = Query(None, ge=0, le=5),
    sort_by: str = Query("date_added_desc", description="Sort field"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get your collection with filtering and search.

    Returns only items owned by authenticated user.
    """
    # Build filters
    filters = {}
    if media_conditions:
        filters["media_conditions"] = media_conditions
    if sleeve_conditions:
        filters["sleeve_conditions"] = sleeve_conditions
    if rating_min is not None:
        filters["rating_min"] = rating_min
    if rating_max is not None:
        filters["rating_max"] = rating_max

    if query:
        # Use search endpoint
        items, total = await service.search_collection(
            user_id=user.sub,
            query=query,
            limit=limit,
            offset=offset
        )
    else:
        # Use filtered listing
        items, total = await service.get_user_collection(
            user_id=user.sub,
            filters=filters if filters else None,
            sort_by=sort_by,
            limit=limit,
            offset=offset
        )

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.put(
    "/{item_id}",
    response_model=CollectionItemResponse,
    summary="Update collection item",
    dependencies=[Depends(require_editor())]
)
async def update_collection_item(
    item_id: UUID,
    item_data: CollectionItemUpdate,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update a collection item.

    SECURITY: Verifies user owns the item.
    """
    updates = item_data.model_dump(exclude_unset=True)
    if "location" in updates:
        updates["storage_location"] = updates.pop("location")
    if "notes" in updates:
        updates["user_notes"] = updates.pop("notes")
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    item = await service.update_collection_item(
        item_id,
        user.sub,
        user_name=user.name,
        user_email=user.email,
        **updates
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection item {item_id} not found or access denied"
        )
    return item


@router.put(
    "/{item_id}/condition",
    response_model=CollectionItemResponse,
    summary="Update item condition",
    dependencies=[Depends(require_editor())]
)
async def update_condition(
    item_id: UUID,
    condition_data: ConditionUpdateRequest,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update condition information for a collection item.

    Uses domain entity business method with validation.
    """
    item = await service.update_condition(
        item_id=item_id,
        user_id=user.sub,
        media_condition=condition_data.media_condition,
        sleeve_condition=condition_data.sleeve_condition,
        defect_notes=condition_data.defect_notes
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection item {item_id} not found or access denied"
        )
    return item


@router.put(
    "/{item_id}/purchase",
    response_model=CollectionItemResponse,
    summary="Update purchase information",
    dependencies=[Depends(require_editor())]
)
async def update_purchase_info(
    item_id: UUID,
    purchase_data: PurchaseInfoUpdateRequest,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update purchase information for a collection item.

    Uses domain entity business method with validation.
    """
    try:
        item = await service.update_purchase_info(
            item_id=item_id,
            user_id=user.sub,
            price=purchase_data.purchase_price,
            currency=purchase_data.purchase_currency,
            purchase_date=purchase_data.purchase_date,
            seller=purchase_data.seller
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection item {item_id} not found or access denied"
            )
        return item
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{item_id}/rating",
    response_model=CollectionItemResponse,
    summary="Update item rating",
    dependencies=[Depends(require_editor())]
)
async def update_rating(
    item_id: UUID,
    rating_data: RatingUpdateRequest,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update rating and notes for a collection item.

    Rating must be 0-5 (domain validation).
    """
    try:
        item = await service.update_rating(
            item_id=item_id,
            user_id=user.sub,
            rating=rating_data.rating,
            notes=rating_data.notes
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection item {item_id} not found or access denied"
            )
        return item
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{item_id}/play",
    response_model=CollectionItemResponse,
    summary="Increment play count",
    dependencies=[Depends(require_editor())]
)
async def increment_play_count(
    item_id: UUID,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Increment play count and update last played timestamp.

    Useful for tracking listening history.
    """
    item = await service.increment_play_count(item_id, user.sub)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection item {item_id} not found or access denied"
        )
    return item


@router.post(
    "/albums/{album_id}/play",
    response_model=AlbumPlayIncrementResponse,
    summary="Increment album play count",
    dependencies=[Depends(require_editor())]
)
async def increment_album_play_count(
    album_id: UUID,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Increment play count for an album for the current user.
    """
    try:
        result = await service.increment_album_play_count(
            album_id=album_id,
            user_id=user.sub
        )
        return AlbumPlayIncrementResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/plays/ytd",
    response_model=PaginatedResponse[PlayedAlbumEntry],
    summary="Get played albums for the year",
    dependencies=[Depends(require_viewer())]
)
async def get_played_albums_ytd(
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)],
    year: int = Query(None, ge=1900, le=2100),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get played albums for the given year (YTD) for the current user.
    """
    resolved_year = year or datetime.utcnow().year
    items, total = await service.get_played_albums_ytd(
        user_id=user.sub,
        year=resolved_year,
        limit=limit,
        offset=offset
    )
    response_items = [PlayedAlbumEntry(**entry) for entry in items]
    return PaginatedResponse(
        items=response_items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.delete(
    "/{item_id}",
    response_model=MessageResponse,
    summary="Remove item from collection",
    dependencies=[Depends(require_editor())]
)
async def remove_from_collection(
    item_id: UUID,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Remove an item from your collection.

    SECURITY: Verifies user owns the item.
    """
    success = await service.remove_from_collection(
        item_id,
        user.sub,
        user_name=user.name,
        user_email=user.email
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection item {item_id} not found or access denied"
        )
    return MessageResponse(message="Item removed from collection successfully")
