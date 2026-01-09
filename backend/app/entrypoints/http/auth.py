"""
Azure Entra ID authentication and group-based authorization.

This module enforces authentication and authorization at the API boundary.
Domain and application layers remain security-agnostic.
"""

from typing import Annotated, List, Optional
from uuid import UUID, uuid5, NAMESPACE_DNS
from fastapi import Depends, HTTPException, status
import logging
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError
from app.config import get_settings, Settings


security = HTTPBearer()
logger = logging.getLogger(__name__)


class User:
    """Authenticated user with group membership."""

    def __init__(
        self,
        sub: UUID,
        email: str,
        groups: List[str],
        name: str | None = None,
        alternate_ids: Optional[List[UUID]] = None
    ):
        self.sub = sub
        self.alternate_ids = [uid for uid in (alternate_ids or []) if uid != sub]

        self.email = email
        self.name = name or email
        self.groups = groups

    def has_group(self, group_id: str) -> bool:
        """Check if user belongs to a specific Azure AD group."""
        return group_id in self.groups

    def has_any_group(self, group_ids: List[str]) -> bool:
        """Check if user belongs to any of the specified groups."""
        return any(group_id in self.groups for group_id in group_ids)


class AuthorizationError(Exception):
    """Raised when user lacks required group membership."""
    pass


def validate_token(token: str, settings: Settings) -> User:
    """
    Validate Azure Entra ID access token and extract user information.

    Validates:
    - Token signature using Azure's public keys
    - Issuer
    - Audience
    - Expiry
    """
    try:
        # Get Azure AD signing keys
        jwks_uri = f"https://login.microsoftonline.com/{settings.azure_tenant_id}/discovery/v2.0/keys"
        jwks_client = PyJWKClient(jwks_uri)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Validate and decode token
        # Accept both v1.0 and v2.0 issuer formats
        valid_issuers = [
            f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0",
            f"https://sts.windows.net/{settings.azure_tenant_id}/",
        ]

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.azure_audience,
            options={"verify_iss": False},  # We'll verify issuer manually
        )

        # Manually verify issuer
        token_issuer = payload.get("iss")
        if token_issuer not in valid_issuers:
            raise jwt.InvalidTokenError(f"Invalid issuer: {token_issuer}")

        def parse_uuid(value: Optional[str]) -> Optional[UUID]:
            if not value:
                return None
            try:
                return UUID(value)
            except ValueError:
                return None

        # Extract user information
        # Prefer 'oid' (object ID) as the primary identifier; fall back to 'sub'
        raw_oid = payload.get("oid")
        raw_sub = payload.get("sub")
        oid_uuid = parse_uuid(raw_oid)
        sub_uuid = parse_uuid(raw_sub)
        user_id = oid_uuid or sub_uuid
        if not user_id:
            source = raw_sub or raw_oid
            if not source:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing oid or sub claim",
                )
            # Generate deterministic UUID from the user identifier string
            user_id = uuid5(NAMESPACE_DNS, f"azure-ad-user:{source}")
        email = payload.get("email") or payload.get("preferred_username")
        name = payload.get("name") or email
        groups = payload.get("groups", [])

        alternate_ids: List[UUID] = []
        if oid_uuid and sub_uuid and oid_uuid != sub_uuid:
            alternate_ids.append(sub_uuid)

        return User(sub=user_id, email=email, groups=groups, name=name, alternate_ids=alternate_ids)

    except jwt.ExpiredSignatureError:
        logger.warning("Auth failed: token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except PyJWKClientError as e:
        logger.error("Auth failed: unable to validate token (JWKS error): %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to validate token: {str(e)}",
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Auth failed: invalid token: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """
    Validate Azure Entra ID access token and extract user information.

    Returns:
        User object with group membership claims
    """
    return validate_token(credentials.credentials, settings)


def require_group(group_id: str):
    """
    Dependency factory for group-based authorization.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_group("admin-group-id"))])
        async def admin_endpoint():
            ...
    """

    async def check_group(user: Annotated[User, Depends(get_current_user)]) -> User:
        if not user.has_group(group_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required group membership",
            )
        return user

    return check_group


def require_any_group(group_ids: List[str]):
    """
    Dependency factory for requiring membership in any of the specified groups.

    Usage:
        @router.get("/resource", dependencies=[Depends(require_any_group(["group1", "group2"]))])
        async def resource_endpoint():
            ...
    """

    async def check_groups(user: Annotated[User, Depends(get_current_user)]) -> User:
        if not user.has_any_group(group_ids):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required group membership",
            )
        return user

    return check_groups
