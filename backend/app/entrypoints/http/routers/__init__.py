"""
API routers for HTTP endpoints.
"""

from .artists import router as artists_router
from .albums import router as albums_router
from .tracks import router as tracks_router
from .pressings import router as pressings_router
from .collection import router as collection_router
from .lookup import router as lookup_router
from .preferences import router as preferences_router
from .system_logs import router as system_logs_router
from .system_logs import internal_router as internal_system_logs_router
from .tools import router as tools_router
from .discogs import router as discogs_router
from .collection_sharing import router as collection_sharing_router
from .album_wizard import router as album_wizard_router

__all__ = [
    "artists_router",
    "albums_router",
    "tracks_router",
    "pressings_router",
    "collection_router",
    "lookup_router",
    "preferences_router",
    "system_logs_router",
    "internal_system_logs_router",
    "tools_router",
    "discogs_router",
    "collection_sharing_router",
    "album_wizard_router",
]
