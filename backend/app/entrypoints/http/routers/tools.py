"""
Admin tools endpoints.
"""

from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.entrypoints.http.authorization import require_admin
from app.entrypoints.http.auth import get_current_user, User
from app.entrypoints.http.dependencies import (
    get_db_session,
    get_discogs_tracklist_sync_service,
    get_system_log_service,
)
from app.entrypoints.http.schemas.common import MessageResponse
from app.application.services.discogs_tracklist_sync_service import DiscogsTracklistSyncService
from app.application.services.system_log_service import SystemLogService
from app.entrypoints.workers.backup_worker import run_backup_now, _build_config


router = APIRouter(prefix="/admin/tools", tags=["Admin Tools"])


class DatabaseCliExecuteRequest(BaseModel):
    """Request payload for database CLI execution."""

    sql: str = Field(..., min_length=1, max_length=20000)
    max_rows: int = Field(default=200, ge=1, le=1000)


class DatabaseCliExecuteResponse(BaseModel):
    """Response payload for database CLI execution."""

    statement_type: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    rows_truncated: bool = False
    affected_rows: int | None = None
    message: str


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


@router.post(
    "/database-cli/execute",
    response_model=DatabaseCliExecuteResponse,
    summary="Execute SQL from admin database CLI",
    dependencies=[Depends(require_admin())],
)
async def execute_database_cli_sql(
    request: DatabaseCliExecuteRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    log_service: Annotated[SystemLogService, Depends(get_system_log_service)],
    user: Annotated[User, Depends(get_current_user)],
):
    raw_sql = request.sql.strip()
    if not raw_sql:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SQL cannot be empty")

    # Keep CLI behavior predictable and avoid stacked statements in one request.
    normalized_sql = raw_sql.rstrip(";").strip()
    if ";" in normalized_sql:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one SQL statement per execution is allowed",
        )

    statement_type = normalized_sql.split(None, 1)[0].upper() if normalized_sql else "UNKNOWN"

    try:
        result = await session.execute(text(raw_sql))
    except Exception as exc:
        await log_service.create_log(
            user_name=user.name or user.email or "*system",
            user_id=user.sub,
            severity="WARN",
            component="Tools",
            message=f"Database CLI failed ({statement_type}): {str(exc)[:240]}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if result.returns_rows:
        mapping_result = result.mappings()
        fetched_rows = mapping_result.fetchmany(request.max_rows + 1)
        rows_truncated = len(fetched_rows) > request.max_rows
        selected_rows = fetched_rows[:request.max_rows]
        rows = [jsonable_encoder(dict(row)) for row in selected_rows]
        columns = list(result.keys())
        row_count = len(rows)
        message = (
            f"Query returned {row_count} rows"
            + (" (truncated)" if rows_truncated else "")
        )
        await log_service.create_log(
            user_name=user.name or user.email or "*system",
            user_id=user.sub,
            severity="INFO",
            component="Tools",
            message=f"Database CLI {statement_type} returned {row_count} rows",
        )
        return DatabaseCliExecuteResponse(
            statement_type=statement_type,
            columns=columns,
            rows=rows,
            row_count=row_count,
            rows_truncated=rows_truncated,
            affected_rows=None,
            message=message,
        )

    affected_rows = result.rowcount if result.rowcount is not None and result.rowcount >= 0 else 0
    await log_service.create_log(
        user_name=user.name or user.email or "*system",
        user_id=user.sub,
        severity="INFO",
        component="Tools",
        message=f"Database CLI {statement_type} affected {affected_rows} rows",
    )
    return DatabaseCliExecuteResponse(
        statement_type=statement_type,
        columns=[],
        rows=[],
        row_count=0,
        rows_truncated=False,
        affected_rows=affected_rows,
        message=f"{statement_type} executed successfully",
    )
