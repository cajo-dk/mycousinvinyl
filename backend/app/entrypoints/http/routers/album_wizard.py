"""
Album Wizard AI endpoints.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.entrypoints.http.authorization import require_viewer
from app.entrypoints.http.auth import User
from app.entrypoints.http.dependencies import (
    get_album_wizard_service,
    get_collection_sharing_service,
)
from app.entrypoints.http.schemas.album_wizard import (
    AlbumWizardScanRequest,
    AlbumWizardScanResponse,
    AlbumWizardAiResult,
    AlbumWizardMatchStatus,
    AlbumWizardArtistMatch,
    AlbumWizardAlbumMatch,
)
from app.entrypoints.http.schemas.collection_sharing import UserOwnerInfoResponse
from app.application.services.album_wizard_service import AlbumWizardService
from app.application.services.collection_sharing_service import CollectionSharingService


router = APIRouter(prefix="/album-wizard", tags=["Album Wizard"])


@router.post(
    "/scan",
    response_model=AlbumWizardScanResponse,
    summary="Scan an album cover image with Album Wizard AI"
)
async def scan_album_cover(
    payload: AlbumWizardScanRequest,
    wizard_service: Annotated[AlbumWizardService, Depends(get_album_wizard_service)],
    sharing_service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    user: Annotated[User, Depends(require_viewer())],
):
    """
    Analyze an album cover image and match it to the catalog.
    """
    try:
        ai_result_raw = await wizard_service.analyze_cover(payload.image_data_url)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Album Wizard AI failed: {exc}"
        ) from exc

    ai_result = AlbumWizardAiResult(**ai_result_raw)

    if not ai_result.image:
        return AlbumWizardScanResponse(
            ai_result=ai_result,
            match_status=AlbumWizardMatchStatus.NO_IMAGE,
            message="No valid album cover detected.",
        )

    match = await wizard_service.match_album(
        artist_name=ai_result.artist,
        album_title=ai_result.album,
        popular_artist=ai_result.popular_artist,
        popular_album=ai_result.popular_album,
    )

    if match.match_status == "no_artist_match":
        return AlbumWizardScanResponse(
            ai_result=ai_result,
            match_status=AlbumWizardMatchStatus.NO_ARTIST_MATCH,
            message="No matching artist found.",
        )

    if match.match_status == "no_album_match":
        return AlbumWizardScanResponse(
            ai_result=ai_result,
            match_status=AlbumWizardMatchStatus.NO_ALBUM_MATCH,
            matched_artist=AlbumWizardArtistMatch(
                id=str(match.artist.id),
                name=match.artist.name,
                sort_name=match.artist.sort_name,
                artist_type=match.artist.type,
            ) if match.artist else None,
            message="No matching album found.",
        )

    owners = []
    if match.album:
        owners_data = await sharing_service.get_owners_for_album(
            user.sub,
            match.album.id,
            user.alternate_ids
        )
        default_display_name = user.name or user.email
        default_first_name = default_display_name.split(" ")[0] if default_display_name else "U"
        owners = [
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
                copy_count=owner.copy_count,
            )
            for owner in owners_data
        ]

    return AlbumWizardScanResponse(
        ai_result=ai_result,
        match_status=AlbumWizardMatchStatus.MATCH_FOUND,
        matched_artist=AlbumWizardArtistMatch(
            id=str(match.artist.id),
            name=match.artist.name,
            sort_name=match.artist.sort_name,
            artist_type=match.artist.type,
        ) if match.artist else None,
        matched_album=AlbumWizardAlbumMatch(
            id=str(match.album.id),
            title=match.album.title,
            release_year=match.album.original_release_year,
            image_url=match.album.image_url,
        ) if match.album else None,
        owners=owners or None,
    )
