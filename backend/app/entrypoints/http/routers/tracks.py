"""
Track API endpoints.
"""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.authorization import require_viewer, require_editor
from app.entrypoints.http.dependencies import get_track_service
from app.entrypoints.http.schemas.track import (
    TrackCreate, TrackUpdate, TrackResponse, TrackReorderRequest
)
from app.entrypoints.http.schemas.common import MessageResponse
from app.application.services.track_service import TrackService


router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.post(
    "",
    response_model=TrackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new track",
    dependencies=[Depends(require_editor())]
)
async def create_track(
    track_data: TrackCreate,
    service: Annotated[TrackService, Depends(get_track_service)]
):
    """
    Create a new track.

    Requires authentication.
    """
    try:
        track = await service.create_track(
            album_id=track_data.album_id,
            side=track_data.side,
            position=track_data.position,
            title=track_data.title,
            duration=track_data.duration,
            credits=track_data.credits
        )
        return track
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{track_id}",
    response_model=TrackResponse,
    summary="Get track by ID",
    dependencies=[Depends(require_viewer())]
)
async def get_track(
    track_id: UUID,
    service: Annotated[TrackService, Depends(get_track_service)]
):
    """
    Get a single track by ID.

    Requires authentication.
    """
    track = await service.get_track(track_id)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track {track_id} not found"
        )
    return track


@router.get(
    "/album/{album_id}",
    response_model=List[TrackResponse],
    summary="Get all tracks for an album",
    dependencies=[Depends(require_viewer())]
)
async def get_album_tracks(
    album_id: UUID,
    service: Annotated[TrackService, Depends(get_track_service)]
):
    """
    Get all tracks for an album, sorted by side and position.

    Requires authentication.
    """
    tracks = await service.get_album_tracks(album_id)
    return tracks


@router.put(
    "/{track_id}",
    response_model=TrackResponse,
    summary="Update a track",
    dependencies=[Depends(require_editor())]
)
async def update_track(
    track_id: UUID,
    track_data: TrackUpdate,
    service: Annotated[TrackService, Depends(get_track_service)]
):
    """
    Update an existing track.

    Requires authentication.
    """
    updates = track_data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    track = await service.update_track(track_id, **updates)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track {track_id} not found"
        )
    return track


@router.post(
    "/album/{album_id}/reorder",
    response_model=MessageResponse,
    summary="Bulk reorder tracks",
    dependencies=[Depends(require_editor())]
)
async def reorder_tracks(
    album_id: UUID,
    reorder_data: TrackReorderRequest,
    service: Annotated[TrackService, Depends(get_track_service)]
):
    """
    Bulk reorder tracks for an album.

    Allows changing side and position for multiple tracks in a single operation.
    Requires authentication.
    """
    track_positions = [
        {
            "track_id": item.track_id,
            "side": item.side,
            "position": item.position
        }
        for item in reorder_data.tracks
    ]

    await service.reorder_tracks(album_id, track_positions)
    return MessageResponse(message="Tracks reordered successfully")


@router.delete(
    "/{track_id}",
    response_model=MessageResponse,
    summary="Delete a track",
    dependencies=[Depends(require_editor())]
)
async def delete_track(
    track_id: UUID,
    service: Annotated[TrackService, Depends(get_track_service)]
):
    """
    Delete a track.

    Requires authentication.
    """
    success = await service.delete_track(track_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track {track_id} not found"
        )
    return MessageResponse(message="Track deleted successfully")
