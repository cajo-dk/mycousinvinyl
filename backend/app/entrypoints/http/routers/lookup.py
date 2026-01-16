"""
Lookup data API endpoints (genres, styles, countries).

Editor-focused endpoints for managing reference data.
"""

from typing import Annotated, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.authorization import require_viewer, require_editor, require_admin
from app.entrypoints.http.dependencies import get_lookup_service, get_system_log_service
from app.entrypoints.http.schemas.lookup import (
    GenreCreate, GenreUpdate, GenreResponse,
    StyleCreate, StyleUpdate, StyleResponse,
    CountryCreate, CountryUpdate, CountryResponse,
    ArtistTypeCreate, ArtistTypeUpdate, ArtistTypeResponse,
    ReleaseTypeCreate, ReleaseTypeUpdate, ReleaseTypeResponse,
    EditionTypeCreate, EditionTypeUpdate, EditionTypeResponse,
    SleeveTypeCreate, SleeveTypeUpdate, SleeveTypeResponse
)
from app.entrypoints.http.schemas.common import MessageResponse
from app.application.services.lookup_service import LookupService
from app.application.services.system_log_service import SystemLogService


router = APIRouter(prefix="/lookup", tags=["Lookup Data"])


# ============================================================================
# GENRE ENDPOINTS
# ============================================================================

@router.get(
    "/genres",
    response_model=List[GenreResponse],
    summary="Get all genres",
    dependencies=[Depends(require_viewer())]
)
async def get_all_genres(
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """
    Get all genres ordered by display_order.

    Requires authentication.
    """
    genres = await service.get_all_genres()
    return genres


@router.get(
    "/genres/{genre_id}",
    response_model=GenreResponse,
    summary="Get genre by ID",
    dependencies=[Depends(require_viewer())]
)
async def get_genre(
    genre_id: UUID,
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """
    Get a specific genre by ID.

    Requires authentication.
    """
    genre = await service.get_genre(genre_id)
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Genre {genre_id} not found"
        )
    return genre


@router.post(
    "/genres",
    response_model=GenreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new genre",
    dependencies=[Depends(require_editor())]
)
async def create_genre(
    genre_data: GenreCreate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Create a new genre.

    Editor operation. Requires authentication.
    """
    genre = await service.create_genre(
        name=genre_data.name,
        display_order=genre_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Created genre '{genre.name}'",
    )
    return genre


@router.put(
    "/genres/{genre_id}",
    response_model=GenreResponse,
    summary="Update a genre",
    dependencies=[Depends(require_editor())]
)
async def update_genre(
    genre_id: UUID,
    genre_data: GenreUpdate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update a genre.

    Editor operation. Requires authentication.
    """
    genre = await service.update_genre(
        genre_id=genre_id,
        name=genre_data.name,
        display_order=genre_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Updated genre '{genre.name}'",
    )
    return genre


@router.delete(
    "/genres/{genre_id}",
    response_model=MessageResponse,
    summary="Delete a genre",
    dependencies=[Depends(require_editor())]
)
async def delete_genre(
    genre_id: UUID,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Delete a genre.

    Will fail if genre is in use by albums (database constraint).
    Editor operation. Requires authentication.
    """
    success = await service.delete_genre(genre_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete genre {genre_id} - it is in use by albums"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Deleted genre {genre_id}",
    )
    return MessageResponse(message="Genre deleted successfully")


# ============================================================================
# STYLE ENDPOINTS
# ============================================================================

@router.get(
    "/styles",
    response_model=List[StyleResponse],
    summary="Get all styles",
    dependencies=[Depends(require_viewer())]
)
async def get_all_styles(
    service: Annotated[LookupService, Depends(get_lookup_service)],
    genre_id: UUID = Query(None, description="Filter by parent genre")
):
    """
    Get all styles, optionally filtered by genre.

    Requires authentication.
    """
    styles = await service.get_all_styles(genre_id=genre_id)
    return styles


@router.get(
    "/styles/{style_id}",
    response_model=StyleResponse,
    summary="Get style by ID",
    dependencies=[Depends(require_viewer())]
)
async def get_style(
    style_id: UUID,
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """
    Get a specific style by ID.

    Requires authentication.
    """
    style = await service.get_style(style_id)
    if not style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Style {style_id} not found"
        )
    return style


@router.post(
    "/styles",
    response_model=StyleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new style",
    dependencies=[Depends(require_editor())]
)
async def create_style(
    style_data: StyleCreate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Create a new style.

    Editor operation. Requires authentication.
    """
    style = await service.create_style(
        name=style_data.name,
        genre_id=style_data.genre_id,
        display_order=style_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Created style '{style.name}'",
    )
    return style


@router.put(
    "/styles/{style_id}",
    response_model=StyleResponse,
    summary="Update a style",
    dependencies=[Depends(require_editor())]
)
async def update_style(
    style_id: UUID,
    style_data: StyleUpdate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update a style.

    Editor operation. Requires authentication.
    """
    style = await service.update_style(
        style_id=style_id,
        name=style_data.name,
        genre_id=style_data.genre_id,
        display_order=style_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Updated style '{style.name}'",
    )
    return style


@router.delete(
    "/styles/{style_id}",
    response_model=MessageResponse,
    summary="Delete a style",
    dependencies=[Depends(require_editor())]
)
async def delete_style(
    style_id: UUID,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Delete a style.

    Will fail if style is in use by albums (database constraint).
    Editor operation. Requires authentication.
    """
    success = await service.delete_style(style_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete style {style_id} - it is in use by albums"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Deleted style {style_id}",
    )
    return MessageResponse(message="Style deleted successfully")


# ============================================================================
# COUNTRY ENDPOINTS
# ============================================================================

@router.get(
    "/countries",
    response_model=List[CountryResponse],
    summary="Get all countries",
    dependencies=[Depends(require_viewer())]
)
async def get_all_countries(
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """
    Get all countries ordered by display_order.

    Requires authentication.
    """
    countries = await service.get_all_countries()
    return countries


@router.get(
    "/countries/{code}",
    response_model=CountryResponse,
    summary="Get country by code",
    dependencies=[Depends(require_viewer())]
)
async def get_country(
    code: str,
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """
    Get a specific country by ISO code.

    Requires authentication.
    """
    country = await service.get_country(code)
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country {code} not found"
        )
    return country


@router.post(
    "/countries",
    response_model=CountryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new country",
    dependencies=[Depends(require_editor())]
)
async def create_country(
    country_data: CountryCreate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Create a new country.

    Editor operation. Requires authentication.
    """
    country = await service.create_country(
        code=country_data.code,
        name=country_data.name,
        display_order=country_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Created country '{country.code}'",
    )
    return country


@router.put(
    "/countries/{code}",
    response_model=CountryResponse,
    summary="Update a country",
    dependencies=[Depends(require_editor())]
)
async def update_country(
    code: str,
    country_data: CountryUpdate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update a country.

    Editor operation. Requires authentication.
    """
    country = await service.update_country(
        code=code,
        name=country_data.name,
        display_order=country_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Updated country '{country.code}'",
    )
    return country


@router.delete(
    "/countries/{code}",
    response_model=MessageResponse,
    summary="Delete a country",
    dependencies=[Depends(require_editor())]
)
async def delete_country(
    code: str,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Delete a country.

    Will fail if country is in use (database constraint).
    Editor operation. Requires authentication.
    """
    success = await service.delete_country(code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete country {code} - it is in use"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Deleted country {code}",
    )
    return MessageResponse(message="Country deleted successfully")


# ============================================================================
# ARTIST TYPE ENDPOINTS
# ============================================================================

@router.get(
    "/artist-types",
    response_model=List[ArtistTypeResponse],
    summary="Get all artist types",
    dependencies=[Depends(require_viewer())]
)
async def get_all_artist_types(
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """Get all artist types ordered by display_order."""
    return await service.get_all_artist_types()


@router.get(
    "/artist-types/{code}",
    response_model=ArtistTypeResponse,
    summary="Get artist type by code",
    dependencies=[Depends(require_viewer())]
)
async def get_artist_type(
    code: str,
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """Get a specific artist type by code."""
    result = await service.get_artist_type(code)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist type {code} not found"
        )
    return result


@router.post(
    "/artist-types",
    response_model=ArtistTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new artist type",
    dependencies=[Depends(require_admin())]
)
async def create_artist_type(
    artist_type_data: ArtistTypeCreate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Create a new artist type."""
    result = await service.create_artist_type(
        code=artist_type_data.code,
        name=artist_type_data.name,
        display_order=artist_type_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Created artist type '{result.code}'",
    )
    return result


@router.put(
    "/artist-types/{code}",
    response_model=ArtistTypeResponse,
    summary="Update an artist type",
    dependencies=[Depends(require_admin())]
)
async def update_artist_type(
    code: str,
    artist_type_data: ArtistTypeUpdate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Update an artist type."""
    result = await service.update_artist_type(
        code=code,
        name=artist_type_data.name,
        display_order=artist_type_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Updated artist type '{result.code}'",
    )
    return result


@router.delete(
    "/artist-types/{code}",
    response_model=MessageResponse,
    summary="Delete an artist type",
    dependencies=[Depends(require_admin())]
)
async def delete_artist_type(
    code: str,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Delete an artist type (fails if in use)."""
    success = await service.delete_artist_type(code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete artist type {code} - it is in use"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Deleted artist type {code}",
    )
    return MessageResponse(message="Artist type deleted successfully")


# ============================================================================
# RELEASE TYPE ENDPOINTS
# ============================================================================

@router.get(
    "/release-types",
    response_model=List[ReleaseTypeResponse],
    summary="Get all release types",
    dependencies=[Depends(require_viewer())]
)
async def get_all_release_types(
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """Get all release types ordered by display_order."""
    return await service.get_all_release_types()


@router.get(
    "/release-types/{code}",
    response_model=ReleaseTypeResponse,
    summary="Get release type by code",
    dependencies=[Depends(require_viewer())]
)
async def get_release_type(
    code: str,
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """Get a specific release type by code."""
    result = await service.get_release_type(code)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Release type {code} not found"
        )
    return result


@router.post(
    "/release-types",
    response_model=ReleaseTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new release type",
    dependencies=[Depends(require_admin())]
)
async def create_release_type(
    release_type_data: ReleaseTypeCreate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Create a new release type."""
    result = await service.create_release_type(
        code=release_type_data.code,
        name=release_type_data.name,
        display_order=release_type_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Created release type '{result.code}'",
    )
    return result


@router.put(
    "/release-types/{code}",
    response_model=ReleaseTypeResponse,
    summary="Update a release type",
    dependencies=[Depends(require_admin())]
)
async def update_release_type(
    code: str,
    release_type_data: ReleaseTypeUpdate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Update a release type."""
    result = await service.update_release_type(
        code=code,
        name=release_type_data.name,
        display_order=release_type_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Updated release type '{result.code}'",
    )
    return result


@router.delete(
    "/release-types/{code}",
    response_model=MessageResponse,
    summary="Delete a release type",
    dependencies=[Depends(require_admin())]
)
async def delete_release_type(
    code: str,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Delete a release type (fails if in use)."""
    success = await service.delete_release_type(code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete release type {code} - it is in use"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Deleted release type {code}",
    )
    return MessageResponse(message="Release type deleted successfully")


# ============================================================================
# EDITION TYPE ENDPOINTS
# ============================================================================

@router.get(
    "/edition-types",
    response_model=List[EditionTypeResponse],
    summary="Get all edition types",
    dependencies=[Depends(require_viewer())]
)
async def get_all_edition_types(
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """Get all edition types ordered by display_order."""
    return await service.get_all_edition_types()


@router.get(
    "/edition-types/{code}",
    response_model=EditionTypeResponse,
    summary="Get edition type by code",
    dependencies=[Depends(require_viewer())]
)
async def get_edition_type(
    code: str,
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """Get a specific edition type by code."""
    result = await service.get_edition_type(code)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edition type {code} not found"
        )
    return result


@router.post(
    "/edition-types",
    response_model=EditionTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new edition type",
    dependencies=[Depends(require_admin())]
)
async def create_edition_type(
    edition_type_data: EditionTypeCreate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Create a new edition type."""
    result = await service.create_edition_type(
        code=edition_type_data.code,
        name=edition_type_data.name,
        display_order=edition_type_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Created edition type '{result.code}'",
    )
    return result


@router.put(
    "/edition-types/{code}",
    response_model=EditionTypeResponse,
    summary="Update an edition type",
    dependencies=[Depends(require_admin())]
)
async def update_edition_type(
    code: str,
    edition_type_data: EditionTypeUpdate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Update an edition type."""
    result = await service.update_edition_type(
        code=code,
        name=edition_type_data.name,
        display_order=edition_type_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Updated edition type '{result.code}'",
    )
    return result


@router.delete(
    "/edition-types/{code}",
    response_model=MessageResponse,
    summary="Delete an edition type",
    dependencies=[Depends(require_admin())]
)
async def delete_edition_type(
    code: str,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Delete an edition type (fails if in use)."""
    success = await service.delete_edition_type(code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete edition type {code} - it is in use"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Deleted edition type {code}",
    )
    return MessageResponse(message="Edition type deleted successfully")


# ============================================================================
# SLEEVE TYPE ENDPOINTS
# ============================================================================

@router.get(
    "/sleeve-types",
    response_model=List[SleeveTypeResponse],
    summary="Get all sleeve types",
    dependencies=[Depends(require_viewer())]
)
async def get_all_sleeve_types(
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """Get all sleeve types ordered by display_order."""
    return await service.get_all_sleeve_types()


@router.get(
    "/sleeve-types/{code}",
    response_model=SleeveTypeResponse,
    summary="Get sleeve type by code",
    dependencies=[Depends(require_viewer())]
)
async def get_sleeve_type(
    code: str,
    service: Annotated[LookupService, Depends(get_lookup_service)]
):
    """Get a specific sleeve type by code."""
    result = await service.get_sleeve_type(code)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sleeve type {code} not found"
        )
    return result


@router.post(
    "/sleeve-types",
    response_model=SleeveTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sleeve type",
    dependencies=[Depends(require_admin())]
)
async def create_sleeve_type(
    sleeve_type_data: SleeveTypeCreate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Create a new sleeve type."""
    result = await service.create_sleeve_type(
        code=sleeve_type_data.code,
        name=sleeve_type_data.name,
        display_order=sleeve_type_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Created sleeve type '{result.code}'",
    )
    return result


@router.put(
    "/sleeve-types/{code}",
    response_model=SleeveTypeResponse,
    summary="Update a sleeve type",
    dependencies=[Depends(require_admin())]
)
async def update_sleeve_type(
    code: str,
    sleeve_type_data: SleeveTypeUpdate,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Update a sleeve type."""
    result = await service.update_sleeve_type(
        code=code,
        name=sleeve_type_data.name,
        display_order=sleeve_type_data.display_order
    )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Updated sleeve type '{result.code}'",
    )
    return result


@router.delete(
    "/sleeve-types/{code}",
    response_model=MessageResponse,
    summary="Delete a sleeve type",
    dependencies=[Depends(require_admin())]
)
async def delete_sleeve_type(
    code: str,
    service: Annotated[LookupService, Depends(get_lookup_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Delete a sleeve type (fails if in use)."""
    success = await service.delete_sleeve_type(code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete sleeve type {code} - it is in use"
        )
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Deleted sleeve type {code}",
    )
    return MessageResponse(message="Sleeve type deleted successfully")
