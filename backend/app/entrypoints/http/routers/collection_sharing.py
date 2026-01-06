"""
Collection Sharing API endpoints.

Manages user follows and collection visibility settings for the collection sharing feature.
SECURITY: User ID extracted from authenticated context, never from request body.
"""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.authorization import require_viewer
from app.entrypoints.http.dependencies import get_collection_sharing_service, get_preferences_service
from app.entrypoints.http.schemas.collection_sharing import (
    CollectionSharingSettingsUpdate,
    CollectionSharingSettingsResponse,
    FollowUserRequest,
    FollowsListResponse,
    UserSearchResponse,
    ItemOwnersResponse,
    UserOwnerInfoResponse,
    PressingOwnersBatchRequest,
    PressingOwnersBatchResponse,
    AlbumOwnersBatchRequest,
    AlbumOwnersBatchResponse
)
from app.application.services.collection_sharing_service import CollectionSharingService
from app.application.services.preferences_service import PreferencesService
from app.domain.value_objects import CollectionSharingSettings


router = APIRouter(prefix="/collection-sharing", tags=["Collection Sharing"])


@router.put(
    "/settings",
    response_model=CollectionSharingSettingsResponse,
    summary="Update collection sharing settings",
    dependencies=[Depends(require_viewer())]
)
async def update_collection_sharing_settings(
    settings_data: CollectionSharingSettingsUpdate,
    service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    prefs_service: Annotated[PreferencesService, Depends(get_preferences_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update collection sharing settings for the current user.

    Allows users to configure:
    - Whether their collection is shared (enabled/disabled)
    - Icon type (MDI alpha icon variant)
    - Icon foreground and background colors

    User ID extracted from authenticated token.
    """
    try:
        # Get current preferences to build updated settings
        preferences = await prefs_service.get_user_preferences(user.sub)

        # Get current settings
        current_settings = preferences.get_collection_sharing_settings()

        # Build updated settings with only changed fields
        updated_settings = CollectionSharingSettings(
            enabled=settings_data.enabled if settings_data.enabled is not None else current_settings.enabled,
            icon_type=settings_data.icon_type if settings_data.icon_type is not None else current_settings.icon_type,
            icon_fg_color=settings_data.icon_fg_color if settings_data.icon_fg_color is not None else current_settings.icon_fg_color,
            icon_bg_color=settings_data.icon_bg_color if settings_data.icon_bg_color is not None else current_settings.icon_bg_color
        )

        # Update preferences
        preferences.update_collection_sharing_settings(updated_settings)
        display_name = user.name or user.email
        first_name = display_name.split(" ")[0] if display_name else "U"
        if "@" in first_name:
            first_name = first_name.split("@")[0]
        preferences.update_user_profile(display_name=display_name, first_name=first_name)
        await prefs_service.update_display_settings(
            user_id=user.sub,
            settings={
                "collection_sharing": preferences.display_settings.get(
                    "collection_sharing", {}
                ),
                "user_profile": preferences.display_settings.get("user_profile", {}),
            }
        )

        # Return updated settings
        return CollectionSharingSettingsResponse(
            enabled=updated_settings.enabled,
            icon_type=updated_settings.icon_type,
            icon_fg_color=updated_settings.icon_fg_color,
            icon_bg_color=updated_settings.icon_bg_color
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/settings",
    response_model=CollectionSharingSettingsResponse,
    summary="Get collection sharing settings",
    dependencies=[Depends(require_viewer())]
)
async def get_collection_sharing_settings(
    prefs_service: Annotated[PreferencesService, Depends(get_preferences_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Get collection sharing settings for the current user.

    Returns the user's sharing configuration including icon and visibility settings.
    User ID extracted from authenticated token.
    """
    preferences = await prefs_service.get_user_preferences(user.sub)
    settings = preferences.get_collection_sharing_settings()

    return CollectionSharingSettingsResponse(
        enabled=settings.enabled,
        icon_type=settings.icon_type,
        icon_fg_color=settings.icon_fg_color,
        icon_bg_color=settings.icon_bg_color
    )


@router.post(
    "/follows",
    status_code=status.HTTP_201_CREATED,
    summary="Follow a user",
    dependencies=[Depends(require_viewer())]
)
async def follow_user(
    follow_request: FollowUserRequest,
    service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Follow another user to see their collection ownership.

    Limitations:
    - Maximum 3 follows per user
    - Cannot follow yourself
    - Can only follow users with sharing enabled

    User ID extracted from authenticated token.
    """
    try:
        followed_user_id = UUID(follow_request.user_id)
        await service.add_follow(user.sub, followed_user_id)
        return {"message": "User followed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/follows/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a user",
    dependencies=[Depends(require_viewer())]
)
async def unfollow_user(
    user_id: UUID,
    service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Unfollow a user.

    Removes the follow relationship. Idempotent - no error if not following.
    User ID extracted from authenticated token.
    """
    await service.remove_follow(user.sub, user_id)
    return None


@router.get(
    "/follows",
    response_model=FollowsListResponse,
    summary="Get followed users",
    dependencies=[Depends(require_viewer())]
)
async def get_follows(
    service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Get list of users that the current user follows.

    Returns user information including icon settings for display.
    User ID extracted from authenticated token.
    """
    follows = await service.get_follows(user.sub)

    # Convert domain objects to response schemas
    follows_response = [
        UserOwnerInfoResponse(
            user_id=str(follow.user_id),
            display_name=follow.display_name,
            first_name=follow.first_name,
            icon_type=follow.icon_type,
            icon_fg_color=follow.icon_fg_color,
            icon_bg_color=follow.icon_bg_color,
            copy_count=follow.copy_count
        )
        for follow in follows
    ]

    return FollowsListResponse(
        follows=follows_response,
        count=len(follows_response)
    )


@router.get(
    "/search",
    response_model=UserSearchResponse,
    summary="Search users by name",
    dependencies=[Depends(require_viewer())]
)
async def search_users(
    service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    user: Annotated[User, Depends(get_current_user)],
    query: str = Query(..., min_length=1, description="Search query (name)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Search for users by name for autocomplete in follow UI.

    Only returns users with collection sharing enabled.
    Excludes the current user from results.
    User ID extracted from authenticated token.
    """
    users = await service.search_users(query, user.sub, limit)

    # Convert domain objects to response schemas
    users_response = [
        UserOwnerInfoResponse(
            user_id=str(u.user_id),
            display_name=u.display_name,
            first_name=u.first_name,
            icon_type=u.icon_type,
            icon_fg_color=u.icon_fg_color,
            icon_bg_color=u.icon_bg_color,
            copy_count=u.copy_count
        )
        for u in users
    ]

    return UserSearchResponse(
        users=users_response,
        count=len(users_response)
    )


@router.get(
    "/owners/pressing/{pressing_id}",
    response_model=ItemOwnersResponse,
    summary="Get owners of a pressing",
    dependencies=[Depends(require_viewer())]
)
async def get_pressing_owners(
    pressing_id: UUID,
    service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Get owners of a specific pressing.

    Returns current user (if they own it) plus followed users with sharing enabled.
    Maximum 4 owners displayed (current user + 3 followed users).
    User ID extracted from authenticated token.
    """
    owners = await service.get_owners_for_pressing(
        user.sub,
        pressing_id,
        user.alternate_ids
    )

    # Convert domain objects to response schemas
    default_display_name = user.name or user.email
    default_first_name = default_display_name.split(" ")[0] if default_display_name else "U"
    owners_response = [
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
        for owner in owners
    ]

    return ItemOwnersResponse(owners=owners_response)


@router.post(
    "/owners/pressings",
    response_model=PressingOwnersBatchResponse,
    summary="Get owners of multiple pressings",
    dependencies=[Depends(require_viewer())]
)
async def get_pressing_owners_batch(
    request: PressingOwnersBatchRequest,
    service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Get owners for multiple pressings in a single request.
    """
    if not request.pressing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pressing_ids must not be empty"
        )

    if len(request.pressing_ids) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pressing_ids cannot exceed 200 items"
        )

    pressing_ids: List[UUID] = []
    seen: set[UUID] = set()
    try:
        for raw_id in request.pressing_ids:
            parsed = UUID(raw_id)
            if parsed in seen:
                continue
            seen.add(parsed)
            pressing_ids.append(parsed)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

    owners_map = await service.get_owners_for_pressings(
        user.sub,
        pressing_ids,
        user.alternate_ids
    )

    default_display_name = user.name or user.email
    default_first_name = default_display_name.split(" ")[0] if default_display_name else "U"

    owners_by_pressing: dict[str, List[UserOwnerInfoResponse]] = {}
    for pressing_id in pressing_ids:
        owners = owners_map.get(pressing_id, [])
        owners_by_pressing[str(pressing_id)] = [
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
            for owner in owners
        ]

    return PressingOwnersBatchResponse(owners_by_pressing=owners_by_pressing)


@router.get(
    "/owners/album/{album_id}",
    response_model=ItemOwnersResponse,
    summary="Get owners of an album",
    dependencies=[Depends(require_viewer())]
)
async def get_album_owners(
    album_id: UUID,
    service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Get owners of a specific album (any pressing).

    Returns current user (if they own it) plus followed users with sharing enabled.
    Maximum 4 owners displayed (current user + 3 followed users).
    User ID extracted from authenticated token.
    """
    owners = await service.get_owners_for_album(
        user.sub,
        album_id,
        user.alternate_ids
    )

    default_display_name = user.name or user.email
    default_first_name = default_display_name.split(" ")[0] if default_display_name else "U"
    owners_response = [
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
        for owner in owners
    ]

    return ItemOwnersResponse(owners=owners_response)


@router.post(
    "/owners/albums",
    response_model=AlbumOwnersBatchResponse,
    summary="Get owners of multiple albums",
    dependencies=[Depends(require_viewer())]
)
async def get_album_owners_batch(
    request: AlbumOwnersBatchRequest,
    service: Annotated[CollectionSharingService, Depends(get_collection_sharing_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Get owners for multiple albums in a single request.
    """
    if not request.album_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="album_ids must not be empty"
        )

    if len(request.album_ids) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="album_ids cannot exceed 200 items"
        )

    album_ids: List[UUID] = []
    seen: set[UUID] = set()
    try:
        for raw_id in request.album_ids:
            parsed = UUID(raw_id)
            if parsed in seen:
                continue
            seen.add(parsed)
            album_ids.append(parsed)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

    owners_map = await service.get_owners_for_albums(
        user.sub,
        album_ids,
        user.alternate_ids
    )

    default_display_name = user.name or user.email
    default_first_name = default_display_name.split(" ")[0] if default_display_name else "U"

    owners_by_album: dict[str, List[UserOwnerInfoResponse]] = {}
    for album_id in album_ids:
        owners = owners_map.get(album_id, [])
        owners_by_album[str(album_id)] = [
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
            for owner in owners
        ]

    return AlbumOwnersBatchResponse(owners_by_album=owners_by_album)
