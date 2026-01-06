import re
import asyncio
import logging
import time
from typing import Optional, Tuple

import httpx
from oauthlib.oauth1 import Client as OAuthClient, SIGNATURE_TYPE_AUTH_HEADER

from app.config import Settings

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, max_per_minute: int):
        self._min_interval = 60.0 / max_per_minute if max_per_minute > 0 else 0.0
        self._lock = asyncio.Lock()
        self._last_request = 0.0

    async def wait(self) -> None:
        if self._min_interval <= 0:
            return
        async with self._lock:
            now = time.monotonic()
            delay = self._min_interval - (now - self._last_request)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_request = time.monotonic()


NATIONALITY_TO_COUNTRY = {
    "american": "United States",
    "british": "United Kingdom",
    "english": "United Kingdom",
    "scottish": "United Kingdom",
    "welsh": "United Kingdom",
    "irish": "Ireland",
    "canadian": "Canada",
    "australian": "Australia",
    "german": "Germany",
    "french": "France",
    "italian": "Italy",
    "spanish": "Spain",
    "japanese": "Japan",
    "korean": "South Korea",
    "chinese": "China",
    "brazilian": "Brazil",
    "mexican": "Mexico",
    "argentinian": "Argentina",
    "swedish": "Sweden",
    "norwegian": "Norway",
    "danish": "Denmark",
    "finnish": "Finland",
    "dutch": "Netherlands",
    "belgian": "Belgium",
    "austrian": "Austria",
    "swiss": "Switzerland",
    "new zealand": "New Zealand",
    "south african": "South Africa",
    "indian": "India",
    "russian": "Russia",
    "polish": "Poland",
    "czech": "Czech Republic",
    "greek": "Greece",
    "portuguese": "Portugal",
    "icelandic": "Iceland",
}

KNOWN_ACTIVE_YEARS = {
    82730: ("1960", "1970"),  # The Beatles
}

COUNTRY_ALIASES = {
    "usa": "United States",
    "u.s.a.": "United States",
    "u.s.": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
}

COUNTRY_NAME_TO_CODE = {
    "United States": "US",
    "United Kingdom": "GB",
    "Germany": "DE",
    "France": "FR",
    "Japan": "JP",
    "Canada": "CA",
    "Australia": "AU",
    "Netherlands": "NL",
    "Sweden": "SE",
    "Italy": "IT",
    "Spain": "ES",
    "Norway": "NO",
    "Denmark": "DK",
    "Belgium": "BE",
    "Austria": "AT",
    "Switzerland": "CH",
    "Ireland": "IE",
    "Poland": "PL",
    "Brazil": "BR",
    "Mexico": "MX",
    "Argentina": "AR",
    "Chile": "CL",
    "New Zealand": "NZ",
    "South Africa": "ZA",
    "South Korea": "KR",
    "China": "CN",
    "India": "IN",
    "Russia": "RU",
    "Czech Republic": "CZ",
    "Hungary": "HU",
}

PRESSING_PLANT_ENTITY_TYPES = {"Pressed By", "Pressing Plant", "Manufactured By", "Made By"}
MASTERING_STUDIO_ENTITY_TYPES = {"Mastered At", "Lacquer Cut At"}
MASTERING_ENGINEER_ROLE_TOKENS = ("mastered by", "lacquer cut by")
SLEEVE_TYPE_TOKENS = {
    "gatefold": "Gatefold",
    "box set": "Box",
    "box": "Box",
    "single": "Single",
}
EDITION_TYPE_TOKENS = {
    "limited": "Limited",
    "numbered": "Numbered",
    "reissue": "Reissue",
    "remastered": "Remaster",
    "remaster": "Remaster",
}
VINYL_COLOR_KEYWORDS = (
    "black",
    "white",
    "red",
    "blue",
    "green",
    "yellow",
    "orange",
    "purple",
    "pink",
    "brown",
    "grey",
    "gray",
    "clear",
    "transparent",
    "translucent",
    "gold",
    "silver",
    "bronze",
)


class DiscogsClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._base_url = settings.discogs_api_base_url.rstrip("/")
        self._limiter = RateLimiter(settings.discogs_rate_limit_per_minute)
        self._import_log_level = settings.discogs_import_log_level

    def _log_import_detail(self, message: str, **data: object) -> None:
        if str(self._import_log_level).upper() != "VERBOSE":
            return
        logger.info("%s | %s", message, data)

    def _sign_request(self, method: str, url: str, params: Optional[dict] = None) -> Tuple[str, dict, dict]:
        headers = {"User-Agent": self._settings.discogs_user_agent}

        # OAuth 1.0a authentication (requires both token and secret)
        if self._settings.discogs_oauth_token and self._settings.discogs_oauth_token_secret:
            logger.info("Using OAuth 1.0a authentication (token + secret with signature)")
            logger.debug(f"OAuth credentials - Consumer Key: {self._settings.discogs_key[:10]}...")
            logger.debug(f"OAuth credentials - Access Token: {self._settings.discogs_oauth_token[:10]}...")
            logger.debug(f"OAuth query params to sign: {params}")

            client = OAuthClient(
                self._settings.discogs_key,
                client_secret=self._settings.discogs_secret,
                resource_owner_key=self._settings.discogs_oauth_token,
                resource_owner_secret=self._settings.discogs_oauth_token_secret,
                signature_type=SIGNATURE_TYPE_AUTH_HEADER,
            )

            # Build URL with query parameters for signing
            if params:
                # Convert params dict to query string
                from urllib.parse import urlencode
                query_string = urlencode(params)
                url_with_params = f"{url}?{query_string}"
            else:
                url_with_params = url

            uri, signed_headers, _ = client.sign(
                url_with_params,  # Sign URL with query parameters included
                http_method=method,
                headers=headers,
            )

            logger.debug(f"OAuth signed URL: {uri}")
            logger.debug(f"OAuth Authorization header: {signed_headers.get('Authorization', 'NOT SET')[:100]}...")

            headers.update(signed_headers)
            # Return original URL (without params) and params separately
            # httpx will add params to the URL
            return url, headers, params or {}

        # Personal Access Token authentication (token only, no secret)
        if self._settings.discogs_oauth_token:
            logger.info("Using Personal Access Token authentication (Discogs token header)")
            headers["Authorization"] = f"Discogs token={self._settings.discogs_oauth_token}"
            return url, headers, params or {}

        # Fallback to key/secret in params (basic authentication)
        logger.info("Using basic authentication (consumer key/secret in query params)")
        params = params or {}
        params.update({
            "key": self._settings.discogs_key,
            "secret": self._settings.discogs_secret,
        })
        return url, headers, params

    async def _get_json_with_retry(
        self,
        url: str,
        headers: dict,
        params: Optional[dict] = None,
        max_attempts: int = 3,
    ) -> dict:
        last_response: Optional[httpx.Response] = None
        for attempt in range(max_attempts):
            async with httpx.AsyncClient(timeout=10.0) as client:
                await self._limiter.wait()
                response = await client.get(url, headers=headers, params=params)
            last_response = response
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = None
                if retry_after:
                    try:
                        delay = int(retry_after)
                    except ValueError:
                        delay = None
                base_delay = 20
                if delay is not None:
                    delay = max(base_delay, delay)
                else:
                    delay = base_delay
                await asyncio.sleep(delay)
                continue
            response.raise_for_status()
            return response.json()

        if last_response is not None:
            last_response.raise_for_status()
        raise RuntimeError("Discogs request failed without a response")

    async def search_artists(self, query: str, limit: int) -> list[dict]:
        params = {"q": query, "type": "artist", "per_page": limit, "page": 1}
        url, headers, signed_params = self._sign_request("GET", f"{self._base_url}/database/search", params)
        data = await self._get_json_with_retry(url, headers, signed_params)
        results = []
        for item in data.get("results", [])[:limit]:
            results.append({
                "id": item.get("id"),
                "name": item.get("title"),
                "thumb_url": item.get("thumb"),
                "uri": item.get("uri"),
                "resource_url": item.get("resource_url"),
            })
        return results

    async def search_albums(self, artist_id: int, query: str, limit: int, page: int = 1) -> dict:
        params = {
            "q": query,
            "type": "master",
            "artist_id": artist_id,
            "per_page": limit,
            "page": page,
        }
        url, headers, signed_params = self._sign_request("GET", f"{self._base_url}/database/search", params)
        data = await self._get_json_with_retry(url, headers, signed_params)

        pagination = data.get("pagination", {})
        results = []
        for item in data.get("results", []):
            results.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "year": item.get("year"),
                "type": item.get("type"),
                "thumb_url": item.get("thumb"),
                "resource_url": item.get("resource_url"),
            })

        return {
            "items": results,
            "total": pagination.get("items", len(results)),
            "page": pagination.get("page", page),
            "pages": pagination.get("pages", 1),
        }

    async def get_artist(self, artist_id: int) -> dict:
        url, headers, signed_params = self._sign_request("GET", f"{self._base_url}/artists/{artist_id}")
        data = await self._get_json_with_retry(url, headers, signed_params)

        profile = data.get("profile") or ""
        begin_date, end_date = _extract_active_years(profile)
        country = _extract_country(profile)
        sort_name = _extract_sort_name(data)
        image_url = _extract_image_url(data)
        artist_type = _extract_artist_type(data)
        if artist_id in KNOWN_ACTIVE_YEARS:
            begin_date, end_date = KNOWN_ACTIVE_YEARS[artist_id]

        self._log_import_detail(
            "Fetched artist details",
            artist_id=artist_id,
            name=data.get("name"),
            country=country,
            begin_date=begin_date,
            end_date=end_date,
            sort_name=sort_name,
            image_url=image_url,
            artist_type=artist_type,
        )

        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "bio": profile.strip() or None,
            "country": country,
            "begin_date": begin_date,
            "end_date": end_date,
            "sort_name": sort_name,
            "image_url": image_url,
            "artist_type": artist_type,
        }

    async def get_album(self, album_id: int, album_type: str) -> dict:
        album_type = album_type or "master"
        endpoint = "masters" if album_type == "master" else "releases"
        url, headers, signed_params = self._sign_request("GET", f"{self._base_url}/{endpoint}/{album_id}")
        data = await self._get_json_with_retry(url, headers, signed_params)

        year = data.get("year")
        country = _normalize_country_code(data.get("country"), fallback_to_original=True)
        genres = data.get("genres") or []
        styles = data.get("styles") or []
        label = None
        catalog_number = None
        labels = data.get("labels") or []
        if labels:
            label = labels[0].get("name")
            catalog_number = labels[0].get("catno")
        images = data.get("images") or []
        image_url = None
        if images:
            primary = next((img for img in images if img.get("type") == "primary"), None)
            selected = primary or images[0]
            image_url = selected.get("uri") or selected.get("uri150")
        release_type = _infer_release_type(data)

        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "year": year,
            "country": country,
            "genres": genres,
            "styles": styles,
            "label": label,
            "catalog_number": catalog_number,
            "image_url": image_url,
            "type": release_type or None,
        }

    async def search_master_releases(self, master_id: int, query: str, limit: int = 25) -> dict:
        """
        Search for releases under a master using Discogs database search.

        Uses Discogs /database/search API with filters:
        - type=release (only releases, not masters/artists/labels)
        - master_id={id} (filter to specific master)
        - q={query} (user's search query for barcode, catalog #, label, etc.)
        """
        # Build URL and params for database search
        url, headers, signed_params = self._sign_request(
            "GET",
            f"{self._base_url}/database/search",
            {
                "type": "release",
                "master_id": master_id,
                "q": query,
                "per_page": limit,
            },
        )

        # Execute search with retry logic
        data = await self._get_json_with_retry(url, headers, signed_params)

        # Fetch master details to get the title
        import logging
        logger = logging.getLogger(__name__)

        master_details = await self.get_album(master_id, "master")
        master_title = master_details.get("title")

        # Extract and normalize results
        results = []
        for item in data.get("results", []):
            # Extract label and catalog number from the label array
            labels = item.get("label") or []
            label = labels[0] if labels else None

            # Get catalog number (catno) from the result
            catalog_number = item.get("catno")

            # Normalize format
            format_value = _normalize_format_list(item.get("format"))

            # Extract barcode - Discogs search returns it as a list
            barcode_value = item.get("barcode")
            barcode = None
            if barcode_value:
                if isinstance(barcode_value, list):
                    # Take the first non-empty barcode from the list
                    barcode = next((b for b in barcode_value if b and str(b).strip()), None)
                else:
                    barcode = str(barcode_value).strip() if barcode_value else None

            results.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "year": item.get("year"),
                "country": item.get("country"),
                "label": label,
                "catalog_number": catalog_number,
                "format": " · ".join(format_value) if format_value else None,
                "barcode": barcode,
                "identifiers": None,  # Not available in search results
                "type": "release",
                "master_id": master_id,
                "master_title": master_title,
                "thumb_url": item.get("thumb"),
                "resource_url": item.get("resource_url"),
            })

        return {
            "items": results,
            "total": data.get("pagination", {}).get("items", len(results)),
        }

    async def get_master_releases(self, master_id: int, page: int = 1, limit: int = 25) -> dict:
        url, headers, signed_params = self._sign_request(
            "GET",
            f"{self._base_url}/masters/{master_id}/versions",
            {"per_page": limit, "page": page},
        )
        try:
            data = await self._get_json_with_retry(url, headers, signed_params)
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                resolved_master_id = await self._resolve_master_id_from_release(master_id)
                if resolved_master_id:
                    logger.info(
                        "Resolved Discogs release %s to master %s for versions lookup",
                        master_id,
                        resolved_master_id,
                    )
                    master_id = resolved_master_id
                    url, headers, signed_params = self._sign_request(
                        "GET",
                        f"{self._base_url}/masters/{master_id}/versions",
                        {"per_page": limit, "page": page},
                    )
                    data = await self._get_json_with_retry(url, headers, signed_params)
                else:
                    raise
            else:
                raise

        # Extract pagination info
        pagination = data.get("pagination", {})
        total_count = pagination.get("items", 0)

        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Pagination data: {pagination}")
        logger.info(f"Total count: {total_count}")

        # Fetch master details to get the title for all releases
        master_details = await self.get_album(master_id, "master")
        master_title = master_details.get("title")

        # Get basic release info from versions endpoint
        versions = data.get("versions", [])[:limit]

        # Fetch full release details for each release to get barcode and identifiers
        # Use asyncio.gather to fetch in parallel for better performance
        import asyncio

        async def fetch_release_details(version_item):
            release_id = version_item.get("id")
            try:
                # Fetch full release details
                release_url, release_headers, release_params = self._sign_request(
                    "GET", f"{self._base_url}/releases/{release_id}"
                )
                release_data = await self._get_json_with_retry(release_url, release_headers, release_params)

                # Extract identifiers and barcode
                labels = release_data.get("labels") or []
                catalog_number = labels[0].get("catno") if labels else None
                identifiers = release_data.get("identifiers") or []
                barcode, identifier_summary = _extract_identifiers(identifiers, catalog_number)

                # Log extracted identifiers for debugging
                logger.info(f"Release {release_id}: barcode={barcode}, identifiers={identifier_summary}")

                format_value = _normalize_format_list(version_item.get("format"))

                return {
                    "id": release_id,
                    "title": version_item.get("title"),
                    "year": version_item.get("year") or _parse_year(version_item.get("released")),
                    "country": version_item.get("country"),
                    "label": version_item.get("label"),
                    "catalog_number": catalog_number,
                    "format": " · ".join(format_value) if format_value else None,
                    "barcode": barcode,
                    "identifiers": identifier_summary,
                    "type": "release",
                    "master_id": master_id,
                    "master_title": master_title,
                    "thumb_url": version_item.get("thumb"),
                    "resource_url": version_item.get("resource_url"),
                }
            except Exception as e:
                # Log the error for debugging
                logger.warning(f"Failed to fetch details for release {release_id}: {str(e)}")
                # If we fail to fetch details, return basic info
                format_value = _normalize_format_list(version_item.get("format"))
                return {
                    "id": release_id,
                    "title": version_item.get("title"),
                    "year": version_item.get("year") or _parse_year(version_item.get("released")),
                    "country": version_item.get("country"),
                    "label": version_item.get("label"),
                    "catalog_number": None,
                    "format": " · ".join(format_value) if format_value else None,
                    "barcode": None,
                    "identifiers": None,
                    "type": "release",
                    "master_id": master_id,
                    "master_title": master_title,
                    "thumb_url": version_item.get("thumb"),
                    "resource_url": version_item.get("resource_url"),
                }

        # Fetch all release details in parallel
        results = await asyncio.gather(*[fetch_release_details(item) for item in versions])
        return {
            "items": list(results),
            "total": total_count,
            "page": pagination.get("page", page),
            "pages": pagination.get("pages", 1),
        }

    async def _resolve_master_id_from_release(self, release_id: int) -> Optional[int]:
        try:
            release = await self.get_release(release_id)
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return None
            raise
        return release.get("master_id") if isinstance(release, dict) else None

    async def get_release(self, release_id: int) -> dict:
        url, headers, signed_params = self._sign_request("GET", f"{self._base_url}/releases/{release_id}")
        data = await self._get_json_with_retry(url, headers, signed_params)

        genres = data.get("genres") or []
        styles = data.get("styles") or []
        labels = data.get("labels") or []
        label = labels[0].get("name") if labels else None
        catalog_number = labels[0].get("catno") if labels else None
        identifiers = data.get("identifiers") or []
        barcode, identifier_summary = _extract_identifiers(identifiers, catalog_number)
        images = data.get("images") or []
        image_url = None
        if images:
            primary = next((img for img in images if img.get("type") == "primary"), None)
            selected = primary or images[0]
            image_url = selected.get("uri") or selected.get("uri150")

        formats = data.get("formats") or []
        format_names = [f.get("name") for f in formats if f.get("name")]
        format_descriptions = []
        format_texts = []
        disc_count = None
        for fmt in formats:
            format_descriptions.extend(fmt.get("descriptions") or [])
            text = fmt.get("text")
            if text:
                format_texts.append(str(text))
            qty = fmt.get("qty")
            if qty:
                try:
                    disc_count = max(disc_count or 0, int(qty))
                except ValueError:
                    pass

        year = data.get("year") or _parse_year(data.get("released"))
        companies = data.get("companies") or []
        extraartists = data.get("extraartists") or []

        raw_vinyl_color = _extract_vinyl_color(format_descriptions, format_texts)
        raw_edition_type = _extract_edition_type(format_descriptions)
        vinyl_color = raw_vinyl_color or "Black"
        edition_type = raw_edition_type or "Standard"

        # Fetch master title if this release has a master_id
        master_id = data.get("master_id")
        master_title = None
        if master_id:
            try:
                master_details = await self.get_album(master_id, "master")
                master_title = master_details.get("title")
            except Exception:
                # If master fetch fails, continue without master_title
                pass

        self._log_import_detail(
            "Fetched release details",
            release_id=release_id,
            title=data.get("title"),
            year=year,
            country=data.get("country"),
            label=label,
            catalog_number=catalog_number,
            format_names=format_names,
            format_descriptions=format_descriptions,
            disc_count=disc_count,
            vinyl_color=vinyl_color,
            vinyl_color_defaulted=raw_vinyl_color is None,
            edition_type=edition_type,
            edition_type_defaulted=raw_edition_type is None,
            master_id=master_id,
            master_title=master_title,
        )

        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "year": year,
            "country": _normalize_country_code(data.get("country"), fallback_to_original=False),
            "genres": genres or None,
            "styles": styles or None,
            "label": label,
            "catalog_number": catalog_number,
            "barcode": barcode,
            "identifiers": identifier_summary,
            "image_url": image_url,
            "formats": format_names or None,
            "format_descriptions": format_descriptions or None,
            "disc_count": disc_count,
            "master_id": master_id,
            "master_title": master_title,
            "pressing_plant": _collect_company_names(companies, PRESSING_PLANT_ENTITY_TYPES),
            "mastering_engineer": _collect_extraartist_names(extraartists, MASTERING_ENGINEER_ROLE_TOKENS),
            "mastering_studio": _collect_company_names(companies, MASTERING_STUDIO_ENTITY_TYPES),
            "vinyl_color": vinyl_color,
            "edition_type": edition_type,
            "sleeve_type": _extract_sleeve_type(format_descriptions),
        }

    async def get_price_suggestions(self, release_id: int) -> Optional[dict]:
        """
        Fetch marketplace price suggestions for a release.

        Uses Discogs /marketplace/price_suggestions/{release_id} endpoint.
        Returns None if pricing data is not available.
        """
        url, headers, signed_params = self._sign_request(
            "GET",
            f"{self._base_url}/marketplace/price_suggestions/{release_id}"
        )

        try:
            data = await self._get_json_with_retry(url, headers, signed_params, max_attempts=2)

            # Discogs returns condition-based pricing like:
            # {"Very Good (VG)": {"currency": "EUR", "value": 4.95}, ...}
            # Extract min, median, max from the suggestions
            if not data:
                return None

            prices = []
            currency = None

            for condition, price_data in data.items():
                if isinstance(price_data, dict) and "value" in price_data:
                    prices.append(price_data["value"])
                    if currency is None and "currency" in price_data:
                        currency = price_data["currency"]

            if not prices:
                return None

            prices.sort()
            median_idx = len(prices) // 2

            return {
                "min_value": min(prices),
                "median_value": prices[median_idx],
                "max_value": max(prices),
                "currency": currency or "USD",
            }

        except httpx.HTTPStatusError as exc:
            # 404 means no pricing data available
            if exc.response.status_code == 404:
                return None
            raise


def _extract_country(profile: str) -> Optional[str]:
    lowered = profile.lower()
    for keyword, country in NATIONALITY_TO_COUNTRY.items():
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            return country

    patterns = [
        r"Country:\s*([A-Za-z .'-]+)",
        r"Born in\s+([A-Za-z .'-]+)",
        r"From\s+([A-Za-z .'-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, profile, re.IGNORECASE)
        if match:
            raw = match.group(1).strip()
            normalized = COUNTRY_ALIASES.get(raw.lower(), raw)
            return normalized
    return None


def _normalize_country_code(value: Optional[str], fallback_to_original: bool = False) -> Optional[str]:
    if not value:
        return None
    trimmed = value.strip()
    if len(trimmed) == 2:
        upper = trimmed.upper()
        if upper == "UK":
            return "GB"
        return upper
    normalized = COUNTRY_ALIASES.get(trimmed.lower(), trimmed)
    resolved = COUNTRY_NAME_TO_CODE.get(normalized)
    if resolved:
        return resolved
    return normalized if fallback_to_original else None


def _extract_active_years(profile: str) -> Tuple[Optional[str], Optional[str]]:
    range_match = re.search(r"([12][0-9]{3})\s*[-–]\s*([12][0-9]{3}|present)", profile, re.IGNORECASE)
    if range_match:
        begin = range_match.group(1)
        end = range_match.group(2)
        return begin, end if end.lower() != "present" else None

    born_match = re.search(r"\bBorn\b.*?([12][0-9]{3})", profile, re.IGNORECASE)
    died_match = re.search(r"\bDied\b.*?([12][0-9]{3})", profile, re.IGNORECASE)

    begin = born_match.group(1) if born_match else None
    end = died_match.group(1) if died_match else None
    if begin or end:
        return begin, end

    formed_match = re.search(
        r"\b(formed|founded|established)\b.*?([12][0-9]{3})",
        profile,
        re.IGNORECASE,
    )
    if formed_match:
        begin = formed_match.group(2)

    disbanded_match = re.search(
        r"\b(disbanded|split|dissolved)\b.*?([12][0-9]{3})",
        profile,
        re.IGNORECASE,
    )
    if disbanded_match:
        end = disbanded_match.group(2)
    return begin, end


def _extract_sort_name(payload: dict) -> Optional[str]:
    for key in ("name_sort", "sort_name"):
        value = payload.get(key)
        if value:
            return str(value).strip()

    variations = payload.get("namevariations") or []
    for candidate in variations:
        if isinstance(candidate, str) and "," in candidate:
            return candidate.strip()
    return None


def _extract_image_url(payload: dict) -> Optional[str]:
    images = payload.get("images") or []
    if not images:
        return None
    primary = next((img for img in images if img.get("type") == "primary"), None)
    selected = primary or images[0]
    return selected.get("uri") or selected.get("uri150")


def _extract_artist_type(payload: dict) -> Optional[str]:
    type_value = payload.get("type")
    if isinstance(type_value, str) and type_value.strip():
        return type_value.strip().title()

    members = payload.get("members") or []
    if members:
        return "Group"

    groups = payload.get("groups") or []
    if groups:
        return "Person"

    return None


def _parse_year(released: Optional[str]) -> Optional[int]:
    if not released:
        return None
    match = re.match(r"^(\d{4})", released)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def _collect_company_names(companies: list[dict], entity_types: set[str]) -> Optional[str]:
    names = []
    for company in companies:
        if company.get("entity_type_name") in entity_types:
            name = company.get("name")
            if name:
                names.append(str(name).strip())
    return _join_unique(names)


def _collect_extraartist_names(extraartists: list[dict], role_tokens: tuple[str, ...]) -> Optional[str]:
    names = []
    for artist in extraartists:
        role = str(artist.get("role") or "").lower()
        if any(token in role for token in role_tokens):
            name = artist.get("name")
            if name:
                names.append(str(name).strip())
    return _join_unique(names)


def _extract_identifiers(identifiers: list[dict], catalog_number: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    lines = []
    barcode = None
    for item in identifiers:
        id_type = str(item.get("type") or "").strip()
        value = str(item.get("value") or "").strip()
        if not id_type or not value:
            continue
        description = str(item.get("description") or "").strip()
        label = f"{id_type} ({description})" if description else id_type
        lines.append(f"{label}: {value}")
        if id_type.lower() == "barcode" and not barcode:
            barcode = value

    if catalog_number:
        lines.append(f"Catalog Number: {catalog_number}")

    formatted = _join_unique(lines, preserve_order=True, separator="\n")
    return barcode, formatted


def _extract_vinyl_color(format_descriptions: list[str], format_texts: list[str]) -> Optional[str]:
    candidates = [*format_texts, *format_descriptions]
    for text in candidates:
        lowered = str(text).lower()
        if any(keyword in lowered for keyword in VINYL_COLOR_KEYWORDS):
            return str(text).strip()
    return None


def _extract_edition_type(format_descriptions: list[str]) -> Optional[str]:
    for desc in format_descriptions:
        lowered = str(desc).lower()
        for token, edition_code in EDITION_TYPE_TOKENS.items():
            if token in lowered:
                return edition_code
    return None


def _extract_sleeve_type(format_descriptions: list[str]) -> Optional[str]:
    for desc in format_descriptions:
        lowered = str(desc).lower()
        for token, sleeve_code in SLEEVE_TYPE_TOKENS.items():
            if token in lowered:
                return sleeve_code
    return None


def _normalize_format_list(value: object) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        return [part for part in parts if part]
    return [str(value).strip()]


def _infer_release_type(payload: dict) -> Optional[str]:
    tokens = []
    raw_format = payload.get("format")
    if raw_format:
        tokens.extend(_normalize_format_list(raw_format))

    formats = payload.get("formats") or []
    for fmt in formats:
        if isinstance(fmt, dict):
            name = fmt.get("name")
            if name:
                tokens.append(str(name))
            for desc in fmt.get("descriptions") or []:
                if desc:
                    tokens.append(str(desc))
            text = fmt.get("text")
            if text:
                tokens.append(str(text))
        elif fmt:
            tokens.append(str(fmt))

    combined = " ".join([token.lower() for token in tokens if token])
    if "compilation" in combined:
        return "Compilation"
    if "live" in combined:
        return "Live"
    if "ep" in combined:
        return "EP"
    if "single" in combined:
        return "Single"
    if "box" in combined:
        return "Box Set"
    if "album" in combined or "studio" in combined:
        return "Studio"
    return None


def _join_unique(values: list[str], preserve_order: bool = True, separator: str = "; ") -> Optional[str]:
    filtered = [value for value in values if value]
    if not filtered:
        return None
    if preserve_order:
        seen = set()
        deduped = []
        for value in filtered:
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(value)
    else:
        deduped = list({value for value in filtered})
    return separator.join(deduped)
