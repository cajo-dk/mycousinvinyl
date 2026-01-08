"""
Scheduled database backup worker.

Creates Postgres backups on configured weekdays/times, uploads to SharePoint,
then removes the local file. Logs success/failure details.
"""

import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx
import msal

from app.logging_config import configure_logging

configure_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 30
UPLOAD_CHUNK_SIZE = 10 * 1024 * 1024
SIMPLE_UPLOAD_MAX_BYTES = 4 * 1024 * 1024


WEEKDAY_MAP = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "weds": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


@dataclass(frozen=True)
class BackupConfig:
    database_url: str
    schedule_days: set[int]
    schedule_time: dt_time
    external_path: Path
    timezone: Optional[ZoneInfo]
    sp_site: str
    sp_library: str
    sp_folder: str
    sp_tenant_id: str
    sp_client_id: str
    sp_client_secret: str


def _parse_schedule_days(value: str) -> set[int]:
    if not value:
        return set()
    tokens = re.split(r"[,\s]+", value.strip())
    days = set()
    for token in tokens:
        if not token:
            continue
        normalized = token.strip().lower()
        if normalized in WEEKDAY_MAP:
            days.add(WEEKDAY_MAP[normalized])
        else:
            logger.warning("Unknown weekday token for backup schedule: %s", token)
    return days


def _parse_schedule_time(value: str) -> Optional[dt_time]:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError:
        logger.error("Invalid BACKUP_SCHEDULE_TIME format (expected HH:MM): %s", value)
        return None
    if parsed.minute % 15 != 0:
        logger.error("BACKUP_SCHEDULE_TIME must be in 15-minute increments: %s", value)
        return None
    return parsed


def _build_config() -> Optional[BackupConfig]:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        logger.error("DATABASE_URL is required for backup worker")
        return None

    schedule_days = _parse_schedule_days(os.getenv("BACKUP_SCHEDULE_DAYS", ""))
    schedule_time = _parse_schedule_time(os.getenv("BACKUP_SCHEDULE_TIME", ""))
    external_path_value = os.getenv("BACKUP_EXTERNAL_PATH", "")
    if not schedule_days or not schedule_time or not external_path_value:
        return None

    return BackupConfig(
        database_url=database_url,
        schedule_days=schedule_days,
        schedule_time=schedule_time,
        external_path=Path(external_path_value),
        timezone=_load_timezone(),
        sp_site=os.getenv("BACKUP_SHAREPOINT_SITE", ""),
        sp_library=os.getenv("BACKUP_SHAREPOINT_LIBRARY", ""),
        sp_folder=os.getenv("BACKUP_SHAREPOINT_FOLDER", ""),
        sp_tenant_id=os.getenv("BACKUP_SHAREPOINT_TENANT_ID", ""),
        sp_client_id=os.getenv("BACKUP_SHAREPOINT_CLIENT_ID", ""),
        sp_client_secret=os.getenv("BACKUP_SHAREPOINT_CLIENT_SECRET", ""),
    )


def _load_timezone() -> Optional[ZoneInfo]:
    tz_name = os.getenv("BACKUP_TIMEZONE", "").strip()
    if not tz_name:
        return None
    try:
        return ZoneInfo(tz_name)
    except Exception:
        logger.error("Invalid BACKUP_TIMEZONE value: %s", tz_name)
        return None


def _now(tz: Optional[ZoneInfo]) -> datetime:
    if tz is None:
        return datetime.now()
    return datetime.now(tz=tz)


def _should_run(now: datetime, schedule_days: set[int], schedule_time: dt_time, last_run_date: Optional[datetime.date]) -> bool:
    if now.weekday() not in schedule_days:
        return False
    if now.hour != schedule_time.hour or now.minute != schedule_time.minute:
        return False
    if last_run_date == now.date():
        return False
    return True


def _ensure_external_path(path: Path) -> bool:
    if not path.exists():
        logger.error("Backup external path does not exist: %s", path)
        return False
    if not path.is_dir():
        logger.error("Backup external path is not a directory: %s", path)
        return False
    if not os.access(path, os.W_OK):
        logger.error("Backup external path is not writable: %s", path)
        return False
    return True


def _pg_dump(database_url: str, output_path: Path) -> None:
    command = [
        "pg_dump",
        "--dbname",
        database_url,
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"pg_dump failed with code {result.returncode}: {stderr}")


def _normalize_sharepoint_site(site: str) -> str:
    site = site.strip()
    if not site:
        return site
    if site.startswith("https://"):
        site = site[len("https://") :]
    if site.startswith("http://"):
        site = site[len("http://") :]
    if "/" in site and ":" not in site:
        parts = site.split("/", 1)
        site = f"{parts[0]}:/{parts[1]}"
    return site


def _get_graph_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret,
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    token = result.get("access_token")
    if not token:
        raise RuntimeError(f"Failed to acquire Graph token: {result.get('error_description')}")
    return token


def _get_site_id(client: httpx.Client, site: str) -> str:
    response = client.get(f"https://graph.microsoft.com/v1.0/sites/{site}")
    response.raise_for_status()
    return response.json()["id"]


def _get_drive_id(client: httpx.Client, site_id: str, library: str) -> str:
    response = client.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives")
    response.raise_for_status()
    drives = response.json().get("value", [])
    for drive in drives:
        if drive.get("name", "").lower() == library.lower():
            return drive["id"]
    raise RuntimeError(f"SharePoint library not found: {library}")


def _upload_simple(client: httpx.Client, drive_id: str, upload_path: str, file_path: Path) -> None:
    url_path = quote(upload_path, safe="/")
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{url_path}:/content"
    with file_path.open("rb") as handle:
        response = client.put(url, content=handle)
        response.raise_for_status()


def _upload_large(client: httpx.Client, drive_id: str, upload_path: str, file_path: Path, size: int) -> None:
    url_path = quote(upload_path, safe="/")
    session_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{url_path}:/createUploadSession"
    response = client.post(session_url, json={"item": {"@microsoft.graph.conflictBehavior": "replace"}})
    response.raise_for_status()
    upload_url = response.json().get("uploadUrl")
    if not upload_url:
        raise RuntimeError("SharePoint upload session did not return uploadUrl")

    with file_path.open("rb") as handle:
        start = 0
        while start < size:
            chunk = handle.read(UPLOAD_CHUNK_SIZE)
            if not chunk:
                break
            end = start + len(chunk) - 1
            headers = {
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {start}-{end}/{size}",
            }
            chunk_response = httpx.put(upload_url, content=chunk, headers=headers, timeout=60.0)
            if chunk_response.status_code in (200, 201):
                return
            if chunk_response.status_code != 202:
                raise RuntimeError(
                    f"SharePoint upload failed: {chunk_response.status_code} {chunk_response.text}"
                )
            start = end + 1


def _upload_to_sharepoint(config: BackupConfig, file_path: Path, size: int) -> None:
    if not (config.sp_site and config.sp_library and config.sp_tenant_id and config.sp_client_id and config.sp_client_secret):
        raise RuntimeError("SharePoint configuration is incomplete")

    site = _normalize_sharepoint_site(config.sp_site)
    token = _get_graph_token(config.sp_tenant_id, config.sp_client_id, config.sp_client_secret)
    headers = {"Authorization": f"Bearer {token}"}

    folder = config.sp_folder.strip().strip("/")
    upload_path = f"{folder}/{file_path.name}" if folder else file_path.name

    with httpx.Client(headers=headers, timeout=60.0) as client:
        site_id = _get_site_id(client, site)
        drive_id = _get_drive_id(client, site_id, config.sp_library)
        if size <= SIMPLE_UPLOAD_MAX_BYTES:
            _upload_simple(client, drive_id, upload_path, file_path)
        else:
            _upload_large(client, drive_id, upload_path, file_path, size)


def _run_backup(config: BackupConfig) -> None:
    start = time.monotonic()
    timestamp = _now(config.timezone).strftime("%Y%m%d_%H%M%S")
    filename = f"mycousinvinyl_backup_{timestamp}.dump"
    backup_path = config.external_path / filename
    size = None

    try:
        if not _ensure_external_path(config.external_path):
            return
        _pg_dump(config.database_url, backup_path)
        size = backup_path.stat().st_size
        _upload_to_sharepoint(config, backup_path, size)
        duration = time.monotonic() - start
        logger.info(
            "Backup succeeded: file=%s size=%s duration=%.2fs",
            backup_path.name,
            size,
            duration,
        )
    except Exception as exc:
        duration = time.monotonic() - start
        logger.error(
            "Backup failed: file=%s size=%s duration=%.2fs error=%s",
            backup_path.name,
            size if size is not None else "unknown",
            duration,
            exc,
            exc_info=True,
        )
    finally:
        if backup_path.exists():
            try:
                backup_path.unlink()
            except Exception:
                logger.error("Failed to remove backup file: %s", backup_path, exc_info=True)


def backup_worker() -> None:
    logger.info("Backup worker started")
    last_run_date = None

    while True:
        try:
            config = _build_config()
            if not config or not config.schedule_days or not config.schedule_time or not config.external_path:
                time.sleep(60)
                continue

            now = _now(config.timezone)
            if _should_run(now, config.schedule_days, config.schedule_time, last_run_date):
                _run_backup(config)
                last_run_date = now.date()
        except Exception as exc:
            logger.error("Backup worker loop error: %s", exc, exc_info=True)

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    backup_worker()
