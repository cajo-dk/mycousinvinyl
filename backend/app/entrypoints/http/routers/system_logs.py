"""
System logs API endpoints (admin only).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException, status, Header

from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.authorization import require_admin
from app.config import get_settings, Settings
from app.entrypoints.http.dependencies import get_system_log_service
from app.entrypoints.http.schemas.common import PaginatedResponse
from app.entrypoints.http.schemas.system_logs import (
    SystemLogEntryResponse,
    LogRetentionResponse,
    LogRetentionUpdate,
    InternalSystemLogCreate,
)
from app.application.services.system_log_service import SystemLogService


router = APIRouter(prefix="/admin", tags=["System Logs"])
internal_router = APIRouter(tags=["System Logs"])


@router.get(
    "/logs",
    response_model=PaginatedResponse[SystemLogEntryResponse],
    summary="List system logs",
    dependencies=[Depends(require_admin())]
)
async def list_system_logs(
    service: Annotated[SystemLogService, Depends(get_system_log_service)],
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    items, total = await service.list_logs(limit=limit, offset=offset)
    response_items = [
        SystemLogEntryResponse(
            id=item.id,
            created_at=item.created_at,
            user_name=item.user_name,
            severity=item.severity,
            component=item.component,
            message=item.message,
        )
        for item in items
    ]
    return PaginatedResponse(
        items=response_items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/log-retention",
    response_model=LogRetentionResponse,
    summary="Get log retention setting",
    dependencies=[Depends(require_admin())]
)
async def get_log_retention(
    service: Annotated[SystemLogService, Depends(get_system_log_service)],
):
    retention_days = await service.get_retention_days()
    return LogRetentionResponse(retention_days=retention_days)


@router.put(
    "/log-retention",
    response_model=LogRetentionResponse,
    summary="Update log retention setting",
    dependencies=[Depends(require_admin())]
)
async def update_log_retention(
    retention: LogRetentionUpdate,
    service: Annotated[SystemLogService, Depends(get_system_log_service)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service, use_cache=False)],
    user: Annotated[User, Depends(get_current_user)],
):
    if retention.retention_days not in {30, 60, 90}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retention must be 30, 60, or 90 days"
        )
    updated = await service.set_retention_days(retention.retention_days)
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Settings",
        message=f"Updated log retention to {updated} days",
    )
    return LogRetentionResponse(retention_days=updated)


@internal_router.post("/internal/logs", status_code=204)
async def create_internal_log(
    entry: InternalSystemLogCreate,
    service: Annotated[SystemLogService, Depends(get_system_log_service)],
    settings: Settings = Depends(get_settings),
    x_system_log_token: str | None = Header(default=None, alias="X-System-Log-Token"),
):
    """Internal endpoint for trusted services to emit system logs."""
    if not settings.system_log_token or x_system_log_token != settings.system_log_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid system log token")

    await service.create_log(
        user_name=entry.user_name or "*system",
        user_id=entry.user_id,
        severity=entry.severity,
        component=entry.component,
        message=entry.message,
    )
