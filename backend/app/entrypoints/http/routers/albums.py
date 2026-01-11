"""
Album API endpoints.
"""

from typing import Annotated, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.authorization import require_viewer, require_editor
from app.entrypoints.http.dependencies import (
    get_album_service,
    get_collection_sharing_service,
    get_preferences_service,
    get_system_log_service,
)
from app.entrypoints.http.schemas.album import (
    AlbumCreate, AlbumUpdate, AlbumResponse, AlbumSearchParams,
    AlbumDetailResponse, ArtistSummaryForAlbum
)
from app.entrypoints.http.schemas.common import PaginatedResponse, MessageResponse
from app.entrypoints.http.schemas.collection_sharing import UserOwnerInfoResponse
from app.application.services.album_service import AlbumService
from app.application.services.collection_sharing_service import CollectionSharingService
from app.application.services.preferences_service import PreferencesService
from app.application.services.system_log_service import SystemLogService


router = APIRouter(prefix="/albums", tags=["Albums"])


@router.post(
    "",
    response_model=AlbumResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new album",
    dependencies=[Depends(require_editor())]
)
async def create_album(
    album_data: AlbumCreate,
    service: Annotated[AlbumService, Depends(get_album_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Create a new album.

    Requires authentication.
    """
    try:
        album = await service.create_album(
            title=album_data.title,
            primary_artist_id=album_data.artist_id,
            release_type=album_data.release_type,
            original_release_year=album_data.release_year,
            country_of_origin=album_data.country_of_origin,
            genre_ids=album_data.genre_ids,
            style_ids=album_data.style_ids,
            label=album_data.label,
            catalog_number_base=album_data.catalog_number,
            description=album_data.notes,
            image_url=album_data.image_url,
            discogs_id=album_data.discogs_id,
            data_source=album_data.data_source,
            created_by=user.sub,
            user_name=user.name,
            user_email=user.email
        )
        await log_service.create_log(
            user_name=user.name or user.email or "*system",
            user_id=user.sub,
            severity="INFO",
            component="Albums",
            message=f"Created album '{album.title}'",
        )
        return album
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/with-details",
    response_model=PaginatedResponse[AlbumDetailResponse],
    summary="Get albums with artist details and pressing counts"
)
async def get_albums_with_details(
    service: Annotated[AlbumService, Depends(get_album_service)],
    sharing_service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    prefs_service: Annotated[PreferencesService, Depends(get_preferences_service)],
    user: Annotated[User, Depends(require_viewer())],
    query: str = Query(None, min_length=1, description="Search albums and artists"),
    artist_id: UUID = Query(None, description="Filter by artist"),
    genre_ids: List[UUID] = Query(None, description="Filter by genres (OR logic)"),
    style_ids: List[UUID] = Query(None, description="Filter by styles (OR logic)"),
    release_type: str = Query(None, description="Filter by release type"),
    year_min: int = Query(None, ge=1900, le=2100),
    year_max: int = Query(None, ge=1900, le=2100),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get albums with enriched artist details and pressing counts.

    Returns albums with joined artist data for hierarchical display.
    Ordered alphabetically by artist (sort_name), then album year, then album title.
    """
    # Extract user ID from authenticated user
    user_id = user.sub

    items_data, total = await service.get_albums_with_details(
        query=query,
        artist_id=artist_id,
        genre_ids=genre_ids,
        style_ids=style_ids,
        release_type=release_type,
        year_min=year_min,
        year_max=year_max,
        limit=limit,
        offset=offset,
        user_id=user_id
    )

    # Transform data into response schema
    response_items = []
    for item_data in items_data:
        album = item_data["album"]
        artist = item_data["artist"]
        genres = item_data["genres"]
        styles = item_data.get("styles", [])
        pressing_count = item_data["pressing_count"]
        in_user_collection = item_data.get("in_user_collection", False)
        owners_info = []
        try:
            owners_data = await sharing_service.get_owners_for_album(
                user.sub,
                album.id,
                user.alternate_ids
            )
            default_display_name = user.name or user.email
            default_first_name = default_display_name.split(" ")[0] if default_display_name else "U"
            owners_info = [
                UserOwnerInfoResponse(
                    user_id=str(owner.user_id),
                    display_name=(
                        default_display_name
                        if owner.user_id == user.sub and owner.display_name == "Unknown User"
                        else owner.display_name
                    ),
                    first_name=(
                        default_first_name
                        if owner.user_id == user.sub and owner.first_name == "U"
                        else owner.first_name
                    ),
                    icon_type=owner.icon_type,
                    icon_fg_color=owner.icon_fg_color,
                    icon_bg_color=owner.icon_bg_color,
                    copy_count=owner.copy_count
                )
                for owner in owners_data
            ]
        except Exception:
            # If collection sharing fails, continue without owners data
            pass
        if in_user_collection and not owners_info:
            prefs = await prefs_service.get_user_preferences(user.sub)
            sharing_settings = prefs.get_collection_sharing_settings()
            user_profile = prefs.get_user_profile()
            display_name = user_profile.get("display_name") or user.name or user.email
            first_name = user_profile.get("first_name") or (display_name.split(" ")[0] if display_name else "U")
            owners_info = [
                UserOwnerInfoResponse(
                    user_id=str(user.sub),
                    display_name=display_name,
                    first_name=first_name,
                    icon_type=sharing_settings.icon_type,
                    icon_fg_color=sharing_settings.icon_fg_color,
                    icon_bg_color=sharing_settings.icon_bg_color,
                    copy_count=1,
                )
            ]

        response_items.append(
            AlbumDetailResponse(
                id=album.id,
                title=album.title,
                artist_id=album.primary_artist_id,
                release_year=album.original_release_year,
                release_type=album.release_type,
                label=album.label,
                catalog_number=album.catalog_number_base,
                image_url=album.image_url,
                discogs_id=album.discogs_id,
                genres=genres,
                styles=styles,
                pressing_count=int(pressing_count),
                in_user_collection=in_user_collection,
                owners=owners_info if owners_info else None,
                created_at=album.created_at,
                updated_at=album.updated_at,
                artist=ArtistSummaryForAlbum(
                    id=artist.id,
                    name=artist.name,
                    sort_name=artist.sort_name,
                    artist_type=artist.type
                )
            )
        )

    return PaginatedResponse(
        items=response_items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{album_id}",
    response_model=AlbumResponse,
    summary="Get album by ID",
    dependencies=[Depends(require_viewer())]
)
async def get_album(
    album_id: UUID,
    service: Annotated[AlbumService, Depends(get_album_service)]
):
    """
    Get a single album by ID with genres and styles.

    Requires authentication.
    """
    album = await service.get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Album {album_id} not found"
        )
    return album


@router.get(
    "",
    response_model=PaginatedResponse[AlbumResponse],
    summary="Search albums",
    dependencies=[Depends(require_viewer())]
)
async def search_albums(
    service: Annotated[AlbumService, Depends(get_album_service)],
    query: str = Query(None, min_length=1, description="Full-text search query"),
    artist_id: UUID = Query(None, description="Filter by artist"),
    genre_ids: List[UUID] = Query(None, description="Filter by genres (OR logic)"),
    style_ids: List[UUID] = Query(None, description="Filter by styles (OR logic)"),
    release_type: str = Query(None, description="Filter by release type"),
    year_min: int = Query(None, ge=1900, le=2100),
    year_max: int = Query(None, ge=1900, le=2100),
    sort_by: str = Query("relevance", description="Sort: relevance, title, year_desc, year_asc"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Search albums with full-text search and advanced filtering.

    Uses PostgreSQL full-text search with relevance ranking.
    Requires authentication.
    """
    filters = {}
    if artist_id:
        filters["artist_id"] = artist_id
    if genre_ids:
        filters["genre_ids"] = genre_ids
    if style_ids:
        filters["style_ids"] = style_ids
    if release_type:
        filters["release_type"] = release_type
    if year_min:
        filters["year_min"] = year_min
    if year_max:
        filters["year_max"] = year_max

    albums, total = await service.search_albums(
        query=query,
        filters=filters if filters else None,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )

    return PaginatedResponse(
        items=albums,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/artist/{artist_id}",
    response_model=PaginatedResponse[AlbumResponse],
    summary="Get albums by artist",
    dependencies=[Depends(require_viewer())]
)
async def get_artist_albums(
    artist_id: UUID,
    service: Annotated[AlbumService, Depends(get_album_service)],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get all albums for a specific artist.

    Requires authentication.
    """
    albums, total = await service.get_artist_albums(
        artist_id=artist_id,
        limit=limit,
        offset=offset
    )

    return PaginatedResponse(
        items=albums,
        total=total,
        limit=limit,
        offset=offset
    )


@router.put(
    "/{album_id}",
    response_model=AlbumResponse,
    summary="Update an album",
    dependencies=[Depends(require_editor())]
)
async def update_album(
    album_id: UUID,
    album_data: AlbumUpdate,
    service: Annotated[AlbumService, Depends(get_album_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update an existing album.

    Requires authentication.
    """
    updates = album_data.model_dump(exclude_unset=True, by_alias=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    try:
        album = await service.update_album(
            album_id,
            user_id=user.sub,
            user_name=user.name,
            user_email=user.email,
            **updates
        )
        if not album:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Album {album_id} not found"
            )
        await log_service.create_log(
            user_name=user.name or user.email or "*system",
            user_id=user.sub,
            severity="INFO",
            component="Albums",
            message=f"Updated album '{album.title}'",
        )
        return album
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{album_id}",
    response_model=MessageResponse,
    summary="Delete an album",
    dependencies=[Depends(require_editor())]
)
async def delete_album(
    album_id: UUID,
    service: Annotated[AlbumService, Depends(get_album_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Delete an album.

    Will fail if album has associated pressings or tracks (database constraint).
    Requires authentication.
    """
    success = await service.delete_album(
        album_id,
        user_id=user.sub,
        user_name=user.name,
        user_email=user.email
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Album {album_id} not found or has associated data"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Albums",
        message=f"Deleted album {album_id}",
    )
    return MessageResponse(message="Album deleted successfully")
