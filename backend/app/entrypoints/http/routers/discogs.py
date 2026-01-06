"""
Discogs integration API endpoints.
"""

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
import httpx

from app.entrypoints.http.authorization import require_editor, require_viewer
from app.entrypoints.http.dependencies import (
    get_discogs_service,
    get_album_service,
    get_discogs_oauth_service,
    get_discogs_pat_service,
)
from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.schemas.discogs import (
    DiscogsArtistSearchResponse,
    DiscogsArtistDetails,
    DiscogsAlbumSearchResponse,
    DiscogsAlbumDetails,
    DiscogsReleaseSearchResponse,
    DiscogsReleaseDetails,
)
from app.entrypoints.http.schemas.discogs_oauth import (
    DiscogsOAuthStartRequest,
    DiscogsOAuthStartResponse,
    DiscogsOAuthStatusResponse,
)
from app.entrypoints.http.schemas.discogs_pat import (
    DiscogsPatConnectRequest,
)
from app.entrypoints.http.schemas.common import MessageResponse
from app.application.services.discogs_service import DiscogsService
from app.application.services.album_service import AlbumService
from app.application.services.discogs_oauth_service import DiscogsOAuthService
from app.application.services.discogs_pat_service import DiscogsPatService
from app.config import get_settings


router = APIRouter(prefix="/discogs", tags=["Discogs"])


@router.get(
    "/oauth/status",
    response_model=DiscogsOAuthStatusResponse,
    summary="Get Discogs OAuth connection status",
    dependencies=[Depends(require_viewer())],
)
async def get_discogs_oauth_status(
    service: Annotated[DiscogsOAuthService, Depends(get_discogs_oauth_service)],
    user: Annotated[User, Depends(get_current_user)],
):
    token = await service.get_status(user.sub)
    if not token:
        return DiscogsOAuthStatusResponse(connected=False)
    return DiscogsOAuthStatusResponse(
        connected=True,
        username=token.discogs_username,
        last_synced_at=token.last_synced_at,
    )


@router.post(
    "/oauth/start",
    response_model=DiscogsOAuthStartResponse,
    summary="Start Discogs OAuth flow",
    dependencies=[Depends(require_viewer())],
)
async def start_discogs_oauth(
    service: Annotated[DiscogsOAuthService, Depends(get_discogs_oauth_service)],
    user: Annotated[User, Depends(get_current_user)],
    payload: DiscogsOAuthStartRequest,
):
    try:
        auth_url = await service.start_authorization(user.sub, payload.redirect_uri)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return DiscogsOAuthStartResponse(authorization_url=auth_url)


@router.get(
    "/oauth/callback",
    summary="Discogs OAuth callback",
)
async def discogs_oauth_callback(
    service: Annotated[DiscogsOAuthService, Depends(get_discogs_oauth_service)],
    oauth_token: str = Query(..., alias="oauth_token"),
    oauth_verifier: str = Query(..., alias="oauth_verifier"),
    state: str | None = Query(None),
):
    settings = get_settings()
    try:
        redirect_uri = await service.complete_authorization(oauth_token, oauth_verifier, state)
        return RedirectResponse(f"{redirect_uri}?discogs=connected")
    except Exception as exc:
        fallback = settings.frontend_base_url.rstrip("/")
        error_url = httpx.URL(f"{fallback}/profile", params={"discogs": "error", "message": str(exc)})
        return RedirectResponse(str(error_url))


@router.delete(
    "/oauth/disconnect",
    response_model=MessageResponse,
    summary="Disconnect Discogs OAuth",
    dependencies=[Depends(require_viewer())],
)
async def disconnect_discogs_oauth(
    service: Annotated[DiscogsOAuthService, Depends(get_discogs_oauth_service)],
    user: Annotated[User, Depends(get_current_user)],
):
    await service.disconnect(user.sub)
    return MessageResponse(message="Discogs connection removed")


@router.post(
    "/pat",
    response_model=MessageResponse,
    summary="Save Discogs personal access token",
    dependencies=[Depends(require_viewer())],
)
async def connect_discogs_pat(
    service: Annotated[DiscogsPatService, Depends(get_discogs_pat_service)],
    user: Annotated[User, Depends(get_current_user)],
    payload: DiscogsPatConnectRequest,
):
    try:
        await service.connect_pat(user.sub, payload.username, payload.token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return MessageResponse(message="Discogs token saved")


@router.get(
    "/artists/search",
    response_model=DiscogsArtistSearchResponse,
    summary="Search Discogs artists",
    dependencies=[Depends(require_editor())],
)
async def search_discogs_artists(
    service: Annotated[DiscogsService, Depends(get_discogs_service)],
    query: str = Query(..., min_length=3, description="Artist name to search"),
    limit: int = Query(3, ge=1, le=10),
):
    try:
        results = await service.search_artists(query=query, limit=limit)
        return DiscogsArtistSearchResponse(items=results)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Discogs service error: {exc}",
        ) from exc


@router.get(
    "/artists/{artist_id}",
    response_model=DiscogsArtistDetails,
    summary="Get Discogs artist details",
    dependencies=[Depends(require_editor())],
)
async def get_discogs_artist(
    artist_id: int,
    service: Annotated[DiscogsService, Depends(get_discogs_service)],
):
    try:
        return await service.get_artist(artist_id)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Discogs service error: {exc}",
    ) from exc


@router.get(
    "/albums/search",
    response_model=DiscogsAlbumSearchResponse,
    summary="Search Discogs albums",
    dependencies=[Depends(require_editor())],
)
async def search_discogs_albums(
    service: Annotated[DiscogsService, Depends(get_discogs_service)],
    artist_id: int = Query(..., ge=1, description="Discogs artist ID"),
    query: str = Query(..., min_length=1, description="Album title to search"),
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    page: int = Query(1, ge=1, description="Page number"),
):
    try:
        results = await service.search_albums(artist_id=artist_id, query=query, limit=limit, page=page)
        return results
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Discogs service error: {exc}",
        ) from exc


@router.get(
    "/albums/{album_id}",
    response_model=DiscogsAlbumDetails,
    summary="Get Discogs album details",
    dependencies=[Depends(require_editor())],
)
async def get_discogs_album(
    album_id: int,
    service: Annotated[DiscogsService, Depends(get_discogs_service)],
    album_type: str = Query("master", alias="type"),
):
    try:
        return await service.get_album(album_id, album_type)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Discogs service error: {exc}",
        ) from exc


@router.get(
    "/masters/{master_id}/releases",
    response_model=DiscogsReleaseSearchResponse,
    summary="Get releases for a Discogs master",
    dependencies=[Depends(require_editor())],
)
async def get_discogs_master_releases(
    master_id: int,
    service: Annotated[DiscogsService, Depends(get_discogs_service)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(25, ge=1, le=100),
):
    try:
        results = await service.get_master_releases(master_id=master_id, page=page, per_page=limit)
        return DiscogsReleaseSearchResponse(
            items=results["items"],
            total=results.get("total"),
            page=results.get("page"),
            pages=results.get("pages"),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Discogs service error: {exc}",
        ) from exc


@router.get(
    "/masters/{master_id}/search",
    response_model=DiscogsReleaseSearchResponse,
    summary="Search releases under a Discogs master",
    dependencies=[Depends(require_editor())],
)
async def search_discogs_master_releases(
    master_id: int,
    service: Annotated[DiscogsService, Depends(get_discogs_service)],
    q: str = Query(..., min_length=4, description="Search query (min 4 characters)"),
    limit: int = Query(25, ge=1, le=100, description="Max results"),
):
    """
    Search for releases under a master by barcode, catalog number, label, etc.

    Only returns releases associated with the specified master.
    """
    try:
        results = await service.search_master_releases(
            master_id=master_id, query=q, limit=limit
        )
        return DiscogsReleaseSearchResponse(
            items=results["items"],
            total=results.get("total", 0),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Discogs service error: {exc}",
        ) from exc


@router.get(
    "/releases/{release_id}",
    response_model=DiscogsReleaseDetails,
    summary="Get Discogs release details",
    dependencies=[Depends(require_editor())],
)
async def get_discogs_release(
    release_id: int,
    service: Annotated[DiscogsService, Depends(get_discogs_service)],
):
    try:
        return await service.get_release(release_id)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Discogs service error: {exc}",
        ) from exc


@router.get(
    "/albums/{album_id}/releases",
    response_model=DiscogsReleaseSearchResponse,
    summary="Get Discogs releases for an album",
    dependencies=[Depends(require_editor())],
)
async def get_album_discogs_releases(
    album_id: UUID,
    album_service: Annotated[AlbumService, Depends(get_album_service)],
    discogs_service: Annotated[DiscogsService, Depends(get_discogs_service)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(25, ge=1, le=100),
):
    """
    Get all Discogs releases for an album by looking up the album's Discogs master ID.

    This endpoint is used when creating a pressing to search for available Discogs releases
    to auto-fill pressing details.
    """
    # Get the album to find its discogs_id
    album = await album_service.get_album(album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Album with ID {album_id} not found",
        )

    if not album.discogs_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Album '{album.title}' does not have a Discogs ID",
        )

    try:
        result = await discogs_service.get_master_releases(master_id=album.discogs_id, page=page, per_page=limit)
        return DiscogsReleaseSearchResponse(
            items=result["items"],
            total=result.get("total"),
            page=result.get("page"),
            pages=result.get("pages"),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Discogs service error: {exc}",
        ) from exc
