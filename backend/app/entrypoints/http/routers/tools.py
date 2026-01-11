"""
Admin tools endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.entrypoints.http.authorization import require_admin
from app.entrypoints.http.schemas.common import MessageResponse
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
