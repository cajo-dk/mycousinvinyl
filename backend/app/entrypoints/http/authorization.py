"""
Authorization configuration and role-based access control.

This module defines the authorization policies for the application.
Roles are mapped to Azure AD groups and enforced at the HTTP entrypoint level.
"""

from typing import Annotated, List, Callable
from fastapi import Depends, HTTPException, status
import logging
from app.config import get_settings, Settings
from app.entrypoints.http.auth import User, get_current_user, require_any_group
from app.entrypoints.http.dependencies import get_preferences_service
from app.application.services.preferences_service import PreferencesService

logger = logging.getLogger(__name__)

# ============================================================================
# ROLE DEFINITIONS
# ============================================================================

class Role:
    """
    Application roles mapped to Azure AD groups.

    - ADMIN: Full system access (user management, system settings)
    - EDITOR: Can create/edit collections, albums, artists, pressings
    - VIEWER: Read-only access to catalog and collections
    """
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


def get_group_ids_for_role(role: str, settings: Settings) -> List[str]:
    """
    Get Azure AD group IDs for a given role.

    Admins inherit all permissions, so they're included in all role checks.
    Editors inherit viewer permissions.
    """
    group_ids = []

    # Admin always included
    if settings.azure_group_admin:
        group_ids.append(settings.azure_group_admin)

    # Add role-specific groups (hierarchy: admin > editor > viewer)
    if role == Role.VIEWER:
        # Viewers can access viewer endpoints, editors and admins inherit this
        if settings.azure_group_editor:
            group_ids.append(settings.azure_group_editor)
        if settings.azure_group_viewer:
            group_ids.append(settings.azure_group_viewer)
    elif role == Role.EDITOR:
        # Only editors (and admins) can access editor endpoints
        if settings.azure_group_editor:
            group_ids.append(settings.azure_group_editor)

    return group_ids


def _is_rbac_strict(settings: Settings) -> bool:
    env = (settings.environment or "").lower()
    return settings.rbac_strict or env == "production"


# ============================================================================
# AUTHORIZATION DEPENDENCIES
# ============================================================================

def require_authenticated() -> Callable:
    """
    Require authenticated user (any valid token).

    Usage:
        @router.get("/resource", dependencies=[Depends(require_authenticated())])
    """
    return get_current_user


def require_admin() -> Callable:
    """
    Require Admin role.

    Usage:
        @router.post("/admin/settings", dependencies=[Depends(require_admin())])
    """
    async def check_admin(
        user: Annotated[User, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
        prefs_service: Annotated[PreferencesService, Depends(get_preferences_service)]
    ) -> User:
        group_ids = get_group_ids_for_role(Role.ADMIN, settings)
        if not group_ids:
            if _is_rbac_strict(settings):
                logger.warning("RBAC blocked: missing group config for admin role")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="RBAC group IDs are not configured",
                )
            # If no groups configured, allow all authenticated users (development mode)
            return user

        if not user.has_any_group(group_ids):
            logger.warning("RBAC denied: admin access for user %s", user.sub)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have required group membership"
            )
        await _ensure_user_profile(user, prefs_service)
        return user

    return check_admin


def require_editor() -> Callable:
    """
    Require Editor or Admin role.

    Usage:
        @router.post("/albums", dependencies=[Depends(require_editor())])
    """
    async def check_editor(
        user: Annotated[User, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
        prefs_service: Annotated[PreferencesService, Depends(get_preferences_service)]
    ) -> User:
        group_ids = get_group_ids_for_role(Role.EDITOR, settings)
        if not group_ids:
            if _is_rbac_strict(settings):
                logger.warning("RBAC blocked: missing group config for editor role")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="RBAC group IDs are not configured",
                )
            # If no groups configured, allow all authenticated users (development mode)
            return user

        if not user.has_any_group(group_ids):
            logger.warning("RBAC denied: editor access for user %s", user.sub)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have required group membership"
            )
        await _ensure_user_profile(user, prefs_service)
        return user

    return check_editor


def require_viewer() -> Callable:
    """
    Require Viewer, Editor, or Admin role (i.e., any authenticated user with group).

    Usage:
        @router.get("/albums", dependencies=[Depends(require_viewer())])
    """
    async def check_viewer(
        user: Annotated[User, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
        prefs_service: Annotated[PreferencesService, Depends(get_preferences_service)]
    ) -> User:
        group_ids = get_group_ids_for_role(Role.VIEWER, settings)
        if not group_ids:
            if _is_rbac_strict(settings):
                logger.warning("RBAC blocked: missing group config for viewer role")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="RBAC group IDs are not configured",
                )
            # If no groups configured, allow all authenticated users (development mode)
            return user

        if not user.has_any_group(group_ids):
            logger.warning("RBAC denied: viewer access for user %s", user.sub)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have required group membership"
            )
        await _ensure_user_profile(user, prefs_service)
        return user

    return check_viewer


# ============================================================================
# AUTHORIZATION POLICY DOCUMENTATION
# ============================================================================

"""
Authorization Policy Matrix:

OPERATION                          | ADMIN | EDITOR | VIEWER
-----------------------------------|-------|--------|--------
View catalog (albums, artists)     |   ✓   |   ✓    |   ✓
View own collection                |   ✓   |   ✓    |   ✓
Add to own collection              |   ✓   |   ✓    |   ✗
Edit own collection items          |   ✓   |   ✓    |   ✗
Delete from own collection         |   ✓   |   ✓    |   ✗
Create albums/artists/pressings    |   ✓   |   ✓    |   ✗
Edit catalog data                  |   ✓   |   ✓    |   ✗
Delete catalog data                |   ✓   |   ✓    |   ✗
Manage lookups (genres, styles)    |   ✓   |   ✓    |   ✗
View other users' collections      |   ✓   |   ✗    |   ✗
Manage preferences                 |   ✓   |   ✓    |   ✓
System administration              |   ✓   |   ✗    |   ✗

Notes:
- All operations require authentication
- Admin role inherits all permissions
- If no groups are configured (development), all authenticated users have full access
- Authorization is enforced at HTTP entrypoint level only
- Domain and application layers remain security-agnostic
"""


async def _ensure_user_profile(user: User, prefs_service: PreferencesService) -> None:
    """Persist user profile data for search/autocomplete."""
    preferences = await prefs_service.get_user_preferences(user.sub)
    display_name = user.name or user.email
    first_name = display_name.split(" ")[0] if display_name else "U"
    profile = preferences.get_user_profile()
    if (
        profile.get("display_name") != display_name
        or profile.get("first_name") != first_name
    ):
        await prefs_service.update_display_settings(
            user_id=user.sub,
            settings={"user_profile": {"display_name": display_name, "first_name": first_name}}
        )
