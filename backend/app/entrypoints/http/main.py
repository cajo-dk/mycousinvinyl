"""
Main FastAPI application.

This module defines the HTTP API entrypoint with authentication
and authorization enforced at the boundary.
"""

from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Annotated
import logging

from app.config import get_settings, Settings
from app.logging_config import configure_logging
from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.routers import (
    artists_router,
    albums_router,
    tracks_router,
    pressings_router,
    collection_router,
    lookup_router,
    preferences_router,
    discogs_router,
    collection_sharing_router,
    album_wizard_router,
)
from app.entrypoints.http.activity_ws import router as activity_ws_router

# Configure logging
configure_logging(get_settings().log_level)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MyCousinVinyl API",
    description="Hexagonal microservice with Azure Entra ID authentication",
    version="1.0.0",
)

# CORS configuration
settings = get_settings()
cors_allow_origins = [
    origin.strip()
    for origin in settings.cors_allow_origins.split(",")
    if origin.strip()
]
cors_allow_origin_regex = settings.cors_allow_origin_regex or None
if not cors_allow_origin_regex and settings.environment.lower() != "production":
    cors_allow_origin_regex = r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_origin_regex=cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ROUTER REGISTRATION
# ============================================================================

# Include all API routers with v1 prefix
app.include_router(artists_router, prefix=settings.api_v1_prefix)
app.include_router(albums_router, prefix=settings.api_v1_prefix)
app.include_router(tracks_router, prefix=settings.api_v1_prefix)
app.include_router(pressings_router, prefix=settings.api_v1_prefix)
app.include_router(collection_router, prefix=settings.api_v1_prefix)
app.include_router(lookup_router, prefix=settings.api_v1_prefix)
app.include_router(preferences_router, prefix=settings.api_v1_prefix)
app.include_router(discogs_router, prefix=settings.api_v1_prefix)
app.include_router(collection_sharing_router, prefix=settings.api_v1_prefix)
app.include_router(album_wizard_router, prefix=settings.api_v1_prefix)
app.include_router(activity_ws_router)


# ============================================================================
# HEALTH AND USER ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint (no authentication required)."""
    return {"status": "healthy", "service": "api"}


@app.get(f"{settings.api_v1_prefix}/me")
async def get_current_user_info(
    user: Annotated[User, Depends(get_current_user)]
):
    """Get current authenticated user information."""
    return {
        "sub": user.sub,
        "email": user.email,
        "groups": user.groups,
    }


# Example protected endpoint
@app.get(f"{settings.api_v1_prefix}/example")
async def example_endpoint(
    user: Annotated[User, Depends(get_current_user)]
):
    """Example authenticated endpoint."""
    return {
        "message": "This is a protected endpoint",
        "user": user.email,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
