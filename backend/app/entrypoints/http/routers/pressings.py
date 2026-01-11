"""
Pressing API endpoints (including matrix and packaging).
"""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.authorization import require_viewer, require_editor
from app.entrypoints.http.dependencies import (
    get_pressing_service,
    get_collection_sharing_service,
    get_system_log_service,
)
from app.entrypoints.http.schemas.pressing import (
    PressingCreate, PressingUpdate, PressingResponse, PressingSearchParams,
    PressingDetailResponse, ArtistSummaryForPressing, AlbumSummaryForPressing,
    MatrixCreate, MatrixResponse, MatrixBulkUpdate,
    PackagingCreateOrUpdate, PackagingResponse
)
from app.entrypoints.http.schemas.common import PaginatedResponse, MessageResponse
from app.entrypoints.http.schemas.collection_sharing import UserOwnerInfoResponse
from app.application.services.pressing_service import PressingService
from app.application.services.collection_sharing_service import CollectionSharingService
from app.application.services.system_log_service import SystemLogService


router = APIRouter(prefix="/pressings", tags=["Pressings"])


# ============================================================================
# PRESSING ENDPOINTS
# ============================================================================

@router.post(
    "",
    response_model=PressingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new pressing",
    dependencies=[Depends(require_editor())]
)
async def create_pressing(
    pressing_data: PressingCreate,
    service: Annotated[PressingService, Depends(get_pressing_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Create a new pressing.

    Requires authentication. User ID tracked as creator.
    """
    try:
        pressing = await service.create_pressing(
            album_id=pressing_data.album_id,
            format=pressing_data.format,
            speed_rpm=pressing_data.speed_rpm,
            size_inches=pressing_data.size_inches,
            disc_count=pressing_data.disc_count,
            import_master_releases=pressing_data.import_master_releases or False,
            created_by=user.sub,
            user_name=user.name,
            user_email=user.email,
            pressing_country=pressing_data.country,
            pressing_year=pressing_data.release_year,
            pressing_plant=pressing_data.pressing_plant,
            mastering_engineer=pressing_data.mastering_engineer,
            mastering_studio=pressing_data.mastering_studio,
            vinyl_color=pressing_data.vinyl_color,
            label_design=pressing_data.label_design,
            image_url=pressing_data.image_url,
            edition_type=pressing_data.edition_type,
            barcode=pressing_data.barcode,
            notes=pressing_data.notes,
            discogs_release_id=pressing_data.discogs_release_id,
            discogs_master_id=pressing_data.discogs_master_id,
            master_title=pressing_data.master_title
        )
        await log_service.create_log(
            user_name=user.name or user.email or "*system",
            user_id=user.sub,
            severity="INFO",
            component="Pressings",
            message=f"Created pressing {pressing.id}",
        )
        return pressing
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/with-details",
    response_model=PaginatedResponse[PressingDetailResponse],
    summary="Get pressings with artist and album details"
)
async def get_pressings_with_details(
    service: Annotated[PressingService, Depends(get_pressing_service)],
    sharing_service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    user: Annotated[User, Depends(require_viewer())],
    query: str = Query(None, min_length=1, description="Search albums and artists"),
    artist_id: UUID = Query(None, description="Filter by artist"),
    album_id: UUID = Query(None, description="Filter by album"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get pressings with enriched artist and album details.

    Returns pressings with joined artist/album data for hierarchical display.
    Ordered alphabetically by artist (sort_name), then album year/title, then pressing year.
    """
    # Extract user ID from authenticated user
    user_id = user.sub

    items_data, total = await service.get_pressings_with_details(
        query=query,
        artist_id=artist_id,
        album_id=album_id,
        limit=limit,
        offset=offset,
        user_id=user_id
    )

    # Transform data into response schema
    response_items = []
    for item_data in items_data:
        pressing = item_data["pressing"]
        album = item_data["album"]
        artist = item_data["artist"]
        packaging = item_data.get("packaging")
        child_count = item_data.get("child_count") or 0
        in_user_collection = item_data.get("in_user_collection", False)

        # Get owners for this pressing
        owners_info = []
        try:
            owners_data = await sharing_service.get_owners_for_pressing(
                user.sub,
                pressing.id,
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

        response_items.append(
            PressingDetailResponse(
                id=pressing.id,
                album_id=pressing.album_id,
                format=pressing.format,
                speed_rpm=pressing.speed_rpm,
                size_inches=pressing.size_inches,
                disc_count=pressing.disc_count,
                country=pressing.pressing_country,
                release_year=pressing.pressing_year,
                pressing_plant=pressing.pressing_plant,
                vinyl_color=pressing.vinyl_color,
                edition_type=pressing.edition_type,
                sleeve_type=packaging.sleeve_type if packaging else None,
                barcode=pressing.barcode,
                notes=pressing.notes,
                image_url=pressing.image_url,
                discogs_release_id=pressing.discogs_release_id,
                discogs_master_id=pressing.discogs_master_id,
                master_title=pressing.master_title,
                is_master=child_count > 0,
                created_at=pressing.created_at,
                updated_at=pressing.updated_at,
                artist=ArtistSummaryForPressing(
                    id=artist.id,
                    name=artist.name,
                    sort_name=artist.sort_name,
                    discogs_id=artist.discogs_id
                ),
                album=AlbumSummaryForPressing(
                    id=album.id,
                    title=album.title,
                    release_year=album.original_release_year,
                    image_url=album.image_url,
                    discogs_id=album.discogs_id
                ),
                in_user_collection=in_user_collection,
                owners=owners_info if owners_info else None
            )
        )

    return PaginatedResponse(
        items=response_items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{pressing_id}",
    response_model=PressingResponse,
    summary="Get pressing by ID",
    dependencies=[Depends(require_viewer())]
)
async def get_pressing(
    pressing_id: UUID,
    service: Annotated[PressingService, Depends(get_pressing_service)]
):
    """
    Get a single pressing by ID with matrices and packaging.

    Requires authentication.
    """
    pressing = await service.get_pressing(pressing_id)
    if not pressing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pressing {pressing_id} not found"
        )
    return pressing


@router.get(
    "/album/{album_id}",
    response_model=PaginatedResponse[PressingResponse],
    summary="Get pressings for an album"
)
async def get_album_pressings(
    album_id: UUID,
    service: Annotated[PressingService, Depends(get_pressing_service)],
    user: Annotated[User, Depends(require_viewer())],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get all pressings for a specific album with collection status.

    Requires authentication.
    """
    # Extract user ID from authenticated user
    user_id = user.sub

    items_data, total = await service.get_pressings_by_album(
        album_id=album_id,
        limit=limit,
        offset=offset,
        user_id=user_id
    )

    # Transform data into response schema
    response_items = []
    for item_data in items_data:
        pressing = item_data["pressing"]
        in_user_collection = item_data.get("in_user_collection", False)

        # Convert domain entity to response schema using Pydantic's from_attributes
        pressing_response = PressingResponse.model_validate(pressing)
        # Add the collection status flag
        pressing_response.in_user_collection = in_user_collection
        response_items.append(pressing_response)

    return PaginatedResponse(
        items=response_items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "",
    response_model=PaginatedResponse[PressingResponse],
    summary="Search pressings",
    dependencies=[Depends(require_viewer())]
)
async def search_pressings(
    service: Annotated[PressingService, Depends(get_pressing_service)],
    format: str = Query(None, description="Filter by format"),
    speed: str = Query(None, description="Filter by speed"),
    size: str = Query(None, description="Filter by size"),
    country: str = Query(None, min_length=2, max_length=2),
    year_min: int = Query(None, ge=1900, le=2100),
    year_max: int = Query(None, ge=1900, le=2100),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Search pressings with filters.

    Requires authentication.
    """
    filters = {}
    if format:
        filters["format"] = format
    if speed:
        filters["speed"] = speed
    if size:
        filters["size"] = size
    if country:
        filters["country"] = country
    if year_min:
        filters["year_min"] = year_min
    if year_max:
        filters["year_max"] = year_max

    pressings, total = await service.search_pressings(
        filters=filters if filters else None,
        limit=limit,
        offset=offset
    )

    return PaginatedResponse(
        items=pressings,
        total=total,
        limit=limit,
        offset=offset
    )


@router.put(
    "/{pressing_id}",
    response_model=PressingResponse,
    summary="Update a pressing",
    dependencies=[Depends(require_editor())]
)
async def update_pressing(
    pressing_id: UUID,
    pressing_data: PressingUpdate,
    service: Annotated[PressingService, Depends(get_pressing_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update an existing pressing.

    Requires authentication.
    """
    updates = pressing_data.model_dump(exclude_unset=True)
    if "country" in updates:
        updates["pressing_country"] = updates.pop("country")
    if "release_year" in updates:
        updates["pressing_year"] = updates.pop("release_year")
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    pressing = await service.update_pressing(
        pressing_id,
        user_id=user.sub,
        user_name=user.name,
        user_email=user.email,
        **updates
    )
    if not pressing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pressing {pressing_id} not found"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Pressings",
        message=f"Updated pressing {pressing.id}",
    )
    return pressing


@router.delete(
    "/{pressing_id}",
    response_model=MessageResponse,
    summary="Delete a pressing",
    dependencies=[Depends(require_editor())]
)
async def delete_pressing(
    pressing_id: UUID,
    service: Annotated[PressingService, Depends(get_pressing_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Delete a pressing.

    Will fail if pressing is in any user collections (database constraint).
    Requires authentication.
    """
    success = await service.delete_pressing(
        pressing_id,
        user_id=user.sub,
        user_name=user.name,
        user_email=user.email
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pressing {pressing_id} not found or is in user collections"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Pressings",
        message=f"Deleted pressing {pressing_id}",
    )
    return MessageResponse(message="Pressing deleted successfully")


# ============================================================================
# MATRIX ENDPOINTS
# ============================================================================

@router.get(
    "/{pressing_id}/matrices",
    response_model=List[MatrixResponse],
    summary="Get matrix codes for a pressing",
    dependencies=[Depends(require_viewer())]
)
async def get_pressing_matrices(
    pressing_id: UUID,
    service: Annotated[PressingService, Depends(get_pressing_service)]
):
    """
    Get all matrix/runout codes for a pressing.

    Requires authentication.
    """
    matrices = await service.get_pressing_matrices(pressing_id)
    return matrices


@router.post(
    "/{pressing_id}/matrices",
    response_model=MatrixResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add matrix code to pressing",
    dependencies=[Depends(require_editor())]
)
async def add_matrix_code(
    pressing_id: UUID,
    matrix_data: MatrixCreate,
    service: Annotated[PressingService, Depends(get_pressing_service)]
):
    """
    Add a matrix/runout code to a pressing.

    Requires authentication.
    """
    try:
        matrix = await service.add_matrix_code(
            pressing_id=pressing_id,
            side=matrix_data.side,
            matrix_code=matrix_data.matrix_code,
            etchings=matrix_data.etchings,
            stamper_info=matrix_data.stamper_info
        )
        return matrix
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{pressing_id}/matrices",
    response_model=List[MatrixResponse],
    summary="Bulk update matrix codes",
    dependencies=[Depends(require_editor())]
)
async def bulk_update_matrices(
    pressing_id: UUID,
    bulk_data: MatrixBulkUpdate,
    service: Annotated[PressingService, Depends(get_pressing_service)]
):
    """
    Bulk update matrix codes for a pressing (replaces all existing).

    Requires authentication.
    """
    matrices_data = [
        {
            "side": m.side,
            "matrix_code": m.matrix_code,
            "etchings": m.etchings,
            "stamper_info": m.stamper_info
        }
        for m in bulk_data.matrices
    ]

    matrices = await service.bulk_update_matrices(pressing_id, matrices_data)
    return matrices


# ============================================================================
# PACKAGING ENDPOINTS
# ============================================================================

@router.get(
    "/{pressing_id}/packaging",
    response_model=PackagingResponse,
    summary="Get packaging details for a pressing",
    dependencies=[Depends(require_viewer())]
)
async def get_pressing_packaging(
    pressing_id: UUID,
    service: Annotated[PressingService, Depends(get_pressing_service)]
):
    """
    Get packaging details for a pressing.

    Requires authentication.
    """
    packaging = await service.get_pressing_packaging(pressing_id)
    if not packaging:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No packaging information for pressing {pressing_id}"
        )
    return packaging


@router.put(
    "/{pressing_id}/packaging",
    response_model=PackagingResponse,
    summary="Add or update packaging details",
    dependencies=[Depends(require_editor())]
)
async def add_or_update_packaging(
    pressing_id: UUID,
    packaging_data: PackagingCreateOrUpdate,
    service: Annotated[PressingService, Depends(get_pressing_service)]
):
    """
    Add or update packaging details for a pressing (upsert operation).

    Requires authentication.
    """
    payload = {
        "sleeve_type": packaging_data.sleeve_type,
        "includes_inner_sleeve": packaging_data.has_inner_sleeve,
        "includes_insert": packaging_data.has_insert,
        "includes_poster": packaging_data.has_poster,
        "stickers": packaging_data.sticker_info,
        "notes": packaging_data.notes,
    }
    try:
        packaging = await service.add_or_update_packaging(
            pressing_id=pressing_id,
            **payload
        )
        return packaging
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
