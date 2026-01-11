"""
User preferences API endpoints.

SECURITY: User ID extracted from authenticated context, never from request body.
"""

from typing import Annotated
from fastapi import APIRouter, Depends

from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.authorization import require_viewer
from app.entrypoints.http.dependencies import get_preferences_service, get_system_log_service
from app.entrypoints.http.schemas.preferences import (
    PreferencesUpdateCurrency, PreferencesUpdateDisplay,
    PreferencesUpdate, PreferencesResponse
)
from app.application.services.preferences_service import PreferencesService
from app.application.services.system_log_service import SystemLogService


router = APIRouter(prefix="/preferences", tags=["User Preferences"])


@router.get(
    "",
    response_model=PreferencesResponse,
    summary="Get user preferences",
    dependencies=[Depends(require_viewer())]
)
async def get_preferences(
    service: Annotated[PreferencesService, Depends(get_preferences_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Get user preferences.

    Creates default preferences if none exist (get-or-create pattern).
    User ID extracted from authenticated token.
    """
    preferences = await service.get_user_preferences(user.sub)
    display_name = user.name or user.email
    first_name = display_name.split(" ")[0] if display_name else "U"
    current_profile = preferences.get_user_profile()
    if (
        current_profile.get("display_name") != display_name
        or current_profile.get("first_name") != first_name
    ):
        await service.update_display_settings(
            user_id=user.sub,
            settings={"user_profile": {"display_name": display_name, "first_name": first_name}}
        )
        preferences = await service.get_user_preferences(user.sub)
    return preferences


@router.put(
    "/currency",
    response_model=PreferencesResponse,
    summary="Update preferred currency",
    dependencies=[Depends(require_viewer())]
)
async def update_currency(
    currency_data: PreferencesUpdateCurrency,
    service: Annotated[PreferencesService, Depends(get_preferences_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update user's preferred currency.

    Validates currency code (3-letter ISO 4217).
    """
    try:
        preferences = await service.update_currency(
            user_id=user.sub,
            currency=currency_data.currency
        )
        await log_service.create_log(
            user_name=user.name or user.email or "*system",
            user_id=user.sub,
            severity="INFO",
            component="Settings",
            message=f"Updated currency to {preferences.currency}",
        )
        return preferences
    except ValueError as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/display",
    response_model=PreferencesResponse,
    summary="Update display settings",
    dependencies=[Depends(require_viewer())]
)
async def update_display_settings(
    display_data: PreferencesUpdateDisplay,
    service: Annotated[PreferencesService, Depends(get_preferences_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update user's display settings.

    Settings stored as JSONB, allowing flexible key-value pairs.
    """
    preferences = await service.update_display_settings(
        user_id=user.sub,
        settings=display_data.display_settings
    )
    return preferences


@router.put(
    "",
    response_model=PreferencesResponse,
    summary="Update multiple preferences",
    dependencies=[Depends(require_viewer())]
)
async def update_preferences(
    preferences_data: PreferencesUpdate,
    service: Annotated[PreferencesService, Depends(get_preferences_service)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Update user preferences (currency and/or display settings).

    Convenience method for updating multiple preferences at once.
    """
    try:
        preferences = await service.update_preferences(
            user_id=user.sub,
            currency=preferences_data.currency,
            display_settings=preferences_data.display_settings
        )
        return preferences
    except ValueError as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
