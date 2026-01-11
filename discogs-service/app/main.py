import logging
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.discogs_client import DiscogsClient
from app.schemas import (
    DiscogsArtistSearchResponse,
    DiscogsArtistDetails,
    DiscogsAlbumSearchResponse,
    DiscogsAlbumDetails,
    DiscogsReleaseSearchResponse,
    DiscogsReleaseDetails,
    DiscogsPriceSuggestionsResponse,
)


settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)
discogs_client = DiscogsClient(settings)

app = FastAPI(
    title="MyCousinVinyl Discogs Service",
    description="Microservice for Discogs API integration",
    version="1.0.0",
)


async def _emit_system_log(severity: str, message: str) -> None:
    if not settings.system_log_token or not settings.system_log_url:
        return
    payload = {
        "user_name": "*system",
        "severity": severity,
        "component": "Discogs",
        "message": message,
    }
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(
                f"{settings.system_log_url}/internal/logs",
                json=payload,
                headers={"X-System-Log-Token": settings.system_log_token},
            )
    except Exception:
        logger.warning("Failed to emit system log", exc_info=True)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "discogs-service"}


@app.get("/artists/search", response_model=DiscogsArtistSearchResponse)
async def search_artists(
    query: str = Query(..., min_length=3),
    limit: int = Query(3, ge=1, le=10),
):
    if not settings.discogs_key or not settings.discogs_secret or not settings.discogs_user_agent:
        raise HTTPException(status_code=500, detail="Discogs credentials are not configured")
    try:
        items = await discogs_client.search_artists(query=query, limit=limit)
        return DiscogsArtistSearchResponse(items=items)
    except Exception as exc:
        await _emit_system_log("ERROR", f"Artist search failed: {exc}")
        logger.exception("Discogs search failed")
        raise HTTPException(status_code=502, detail="Failed to reach Discogs") from exc


@app.get("/artists/{artist_id}", response_model=DiscogsArtistDetails)
async def get_artist(artist_id: int):
    if not settings.discogs_key or not settings.discogs_secret or not settings.discogs_user_agent:
        raise HTTPException(status_code=500, detail="Discogs credentials are not configured")
    try:
        return await discogs_client.get_artist(artist_id)
    except Exception as exc:
        await _emit_system_log("ERROR", f"Artist lookup failed: {exc}")
        logger.exception("Discogs artist lookup failed")
        raise HTTPException(status_code=502, detail="Failed to reach Discogs") from exc


@app.get("/albums/search", response_model=DiscogsAlbumSearchResponse)
async def search_albums(
    artist_id: int = Query(..., ge=1),
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    if not settings.discogs_key or not settings.discogs_secret or not settings.discogs_user_agent:
        raise HTTPException(status_code=500, detail="Discogs credentials are not configured")
    try:
        response = await discogs_client.search_albums(artist_id=artist_id, query=query, limit=limit, page=page)
        return response
    except Exception as exc:
        await _emit_system_log("ERROR", f"Album search failed: {exc}")
        logger.exception("Discogs album search failed")
        raise HTTPException(status_code=502, detail="Failed to reach Discogs") from exc


@app.get("/albums/{album_id}", response_model=DiscogsAlbumDetails)
async def get_album(
    album_id: int,
    album_type: str = Query("master", alias="type"),
):
    if not settings.discogs_key or not settings.discogs_secret or not settings.discogs_user_agent:
        raise HTTPException(status_code=500, detail="Discogs credentials are not configured")
    try:
        return await discogs_client.get_album(album_id, album_type)
    except Exception as exc:
        await _emit_system_log("ERROR", f"Album lookup failed: {exc}")
        logger.exception("Discogs album lookup failed")
        raise HTTPException(status_code=502, detail="Failed to reach Discogs") from exc


@app.get("/masters/{master_id}/releases")
async def get_master_releases(
    master_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
):
    if not settings.discogs_key or not settings.discogs_secret or not settings.discogs_user_agent:
        raise HTTPException(status_code=500, detail="Discogs credentials are not configured")
    try:
        response = await discogs_client.get_master_releases(master_id=master_id, page=page, limit=limit)
        logger.info(f"Raw response from client: {response}")
        logger.info(f"Response keys: {response.keys()}")
        logger.info(f"Total value: {response.get('total')}")

        # Use JSONResponse to bypass response model serialization
        return JSONResponse(content={
            "items": response["items"],
            "total": response.get("total"),
            "page": response.get("page"),
            "pages": response.get("pages"),
        })
    except Exception as exc:
        await _emit_system_log("ERROR", f"Master releases lookup failed: {exc}")
        logger.exception("Discogs master releases lookup failed")
        raise HTTPException(status_code=502, detail="Failed to reach Discogs") from exc


@app.get("/masters/{master_id}/search")
async def search_master_releases(
    master_id: int,
    q: str = Query(..., min_length=4, description="Search query (min 4 chars)"),
    limit: int = Query(25, ge=1, le=100),
):
    """
    Search for releases under a master by barcode, catalog number, label, etc.

    Uses Discogs database search API filtered to this master's releases only.
    """
    if not settings.discogs_key or not settings.discogs_secret or not settings.discogs_user_agent:
        raise HTTPException(status_code=500, detail="Discogs credentials are not configured")
    try:
        response = await discogs_client.search_master_releases(
            master_id=master_id, query=q, limit=limit
        )
        return JSONResponse(content=response)
    except Exception as exc:
        await _emit_system_log("ERROR", f"Master releases search failed: {exc}")
        logger.exception("Discogs master releases search failed")
        raise HTTPException(status_code=502, detail="Failed to reach Discogs") from exc


@app.get("/releases/{release_id}", response_model=DiscogsReleaseDetails)
async def get_release(release_id: int):
    if not settings.discogs_key or not settings.discogs_secret or not settings.discogs_user_agent:
        raise HTTPException(status_code=500, detail="Discogs credentials are not configured")
    try:
        return await discogs_client.get_release(release_id)
    except httpx.HTTPStatusError as exc:
        if exc.response is not None and exc.response.status_code == 429:
            await _emit_system_log("WARN", f"Discogs rate limit reached for release {release_id}")
            raise HTTPException(status_code=429, detail="Discogs rate limit reached") from exc
        await _emit_system_log("ERROR", f"Release lookup failed: {exc}")
        logger.exception("Discogs release lookup failed")
        raise HTTPException(status_code=502, detail="Failed to reach Discogs") from exc
    except Exception as exc:
        await _emit_system_log("ERROR", f"Release lookup failed: {exc}")
        logger.exception("Discogs release lookup failed")
        raise HTTPException(status_code=502, detail="Failed to reach Discogs") from exc


@app.get("/marketplace/price_suggestions/{release_id}", response_model=DiscogsPriceSuggestionsResponse)
async def get_price_suggestions(release_id: int):
    """
    Get marketplace price suggestions for a release.

    Returns min, median, max prices and currency.
    Returns 404 if pricing data is not available.
    """
    if not settings.discogs_key or not settings.discogs_secret or not settings.discogs_user_agent:
        raise HTTPException(status_code=500, detail="Discogs credentials are not configured")

    # Personal access token or OAuth credentials required for marketplace endpoints
    if not settings.discogs_oauth_token:
        raise HTTPException(
            status_code=500,
            detail="Personal access token or OAuth credentials required for marketplace API"
        )

    try:
        pricing = await discogs_client.get_price_suggestions(release_id)
    except httpx.HTTPStatusError as exc:
        if exc.response is not None and exc.response.status_code == 429:
            await _emit_system_log("WARN", f"Discogs rate limit reached for release {release_id}")
            raise HTTPException(status_code=429, detail="Discogs rate limit reached") from exc
        if exc.response is not None and exc.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"No marketplace pricing available for release {release_id}"
            ) from exc
        await _emit_system_log("ERROR", f"Price lookup failed: {exc}")
        logger.exception("Discogs price lookup failed")
        raise HTTPException(status_code=502, detail="Failed to reach Discogs") from exc
    except Exception as exc:
        await _emit_system_log("ERROR", f"Price lookup failed: {exc}")
        logger.exception("Discogs price lookup failed")
        raise HTTPException(status_code=502, detail="Failed to reach Discogs") from exc

    # Handle None response (no pricing available)
    if pricing is None:
        raise HTTPException(
            status_code=404,
            detail=f"No marketplace pricing available for release {release_id}"
        )

    return pricing
