"""
Admin tools endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.entrypoints.http.authorization import require_admin
from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.dependencies import get_discogs_tracklist_sync_service, get_system_log_service
from app.entrypoints.http.schemas.common import MessageResponse
from app.application.services.discogs_tracklist_sync_service import DiscogsTracklistSyncService
from app.application.services.system_log_service import SystemLogService
from app.entrypoints.workers.backup_worker import run_backup_now, _build_config


router = APIRouter(prefix="/admin/tools", tags=["Admin Tools"])


@router.post(
    "/backup",
    response_model=MessageResponse,
    summary="Run backup immediately",
    dependencies=[Depends(require_admin())]
)
async def run_backup(background_tasks: BackgroundTasks):
    if not _build_config(require_schedule=False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup configuration is incomplete",
        )
    background_tasks.add_task(run_backup_now)
    return MessageResponse(message="Backup started")


@router.post(
    "/tracklist-sync",
    response_model=MessageResponse,
    summary="Sync all album tracklists from Discogs",
    dependencies=[Depends(require_admin())]
)
async def run_tracklist_sync(
    sync_service: Annotated[DiscogsTracklistSyncService, Depends(get_discogs_tracklist_sync_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)],
):
    summary = await sync_service.sync_all()
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Tools",
        message=(
            "Manual tracklist sync completed: "
            f"checked={summary['total_checked']}, synced={summary['synced']}, "
            f"skipped={summary['skipped']}, failed={summary['failed']}"
        ),
    )
    return MessageResponse(
        message=(
            "Tracklist sync finished. "
            f"Checked {summary['total_checked']}, synced {summary['synced']}, "
            f"skipped {summary['skipped']}, failed {summary['failed']}."
        )
    )
