"""
Artist API endpoints.
"""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.authorization import require_viewer, require_editor
from app.entrypoints.http.dependencies import get_artist_service, get_system_log_service
from app.entrypoints.http.schemas.artist import (
    ArtistCreate, ArtistUpdate, ArtistResponse, ArtistSearchParams
)
from app.entrypoints.http.schemas.common import PaginatedResponse, MessageResponse
from app.application.services.artist_service import ArtistService
from app.application.services.system_log_service import SystemLogService


router = APIRouter(prefix="/artists", tags=["Artists"])


@router.post(
    "",
    response_model=ArtistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new artist",
    dependencies=[Depends(require_editor())]
)
async def create_artist(
    artist_data: ArtistCreate,
    service: Annotated[ArtistService, Depends(get_artist_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Create a new artist.

    Requires authentication.
    """
    artist = await service.create_artist(
        name=artist_data.name,
        type=artist_data.artist_type,
        sort_name=artist_data.sort_name,
        country=artist_data.country,
        disambiguation=artist_data.disambiguation,
        bio=artist_data.bio,
        image_url=artist_data.image_url,
        begin_date=artist_data.begin_date,
        end_date=artist_data.end_date,
        discogs_id=artist_data.discogs_id,
        data_source=artist_data.data_source,
        created_by=user.sub,
        user_name=user.name,
        user_email=user.email
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Artists",
        message=f"Created artist '{artist.name}'",
    )
    return artist


@router.get(
    "/{artist_id}",
    response_model=ArtistResponse,
    summary="Get artist by ID",
    dependencies=[Depends(require_viewer())]
)
async def get_artist(
    artist_id: UUID,
    service: Annotated[ArtistService, Depends(get_artist_service)]
):
    """
    Get a single artist by ID.

    Requires authentication.
    """
    artist = await service.get_artist(artist_id)
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist {artist_id} not found"
        )
    return artist


@router.get(
    "",
    response_model=PaginatedResponse[ArtistResponse],
    summary="Search artists",
    dependencies=[Depends(require_viewer())]
)
async def search_artists(
    service: Annotated[ArtistService, Depends(get_artist_service)],
    query: str = Query(None, min_length=1, description="Fuzzy name search"),
    artist_type: str = Query(None, description="Filter by artist type"),
    country: str = Query(None, min_length=2, max_length=2, description="Filter by country code"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Search artists with fuzzy name matching and filters.

    Requires authentication.
    """
    if query:
        artists, total = await service.search_artists(
            query=query,
            limit=limit,
            offset=offset,
            artist_type=artist_type,
            country=country
        )
    else:
        artists, total = await service.list_artists(
            limit=limit,
            offset=offset,
            artist_type=artist_type,
            country=country
        )

    return PaginatedResponse(
        items=artists,
        total=total,
        limit=limit,
        offset=offset
    )


@router.put(
    "/{artist_id}",
    response_model=ArtistResponse,
    summary="Update an artist",
    dependencies=[Depends(require_editor())]
)
async def update_artist(
    artist_id: UUID,
    artist_data: ArtistUpdate,
    service: Annotated[ArtistService, Depends(get_artist_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update an existing artist.

    Requires authentication.
    """
    updates = artist_data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    artist = await service.update_artist(
        artist_id,
        user_id=user.sub,
        user_name=user.name,
        user_email=user.email,
        **updates
    )
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist {artist_id} not found"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Artists",
        message=f"Updated artist '{artist.name}'",
    )
    return artist


@router.delete(
    "/{artist_id}",
    response_model=MessageResponse,
    summary="Delete an artist",
    dependencies=[Depends(require_editor())]
)
async def delete_artist(
    artist_id: UUID,
    service: Annotated[ArtistService, Depends(get_artist_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Delete an artist.

    Will fail if artist has associated albums (database constraint).
    Requires authentication.
    """
    success = await service.delete_artist(
        artist_id,
        user_id=user.sub,
        user_name=user.name,
        user_email=user.email
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist {artist_id} not found or has associated albums"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Artists",
        message=f"Deleted artist {artist_id}",
    )
    return MessageResponse(message="Artist deleted successfully")
