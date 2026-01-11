"""System log API schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SystemLogEntryResponse(BaseModel):
    id: UUID
    created_at: datetime
    user_name: str
    severity: Literal["INFO", "WARN", "ERROR"]
    component: str
    message: str


class LogRetentionResponse(BaseModel):
    retention_days: int = Field(..., ge=1)


class LogRetentionUpdate(BaseModel):
    retention_days: int = Field(..., ge=1)


class InternalSystemLogCreate(BaseModel):
    user_name: str = Field(default="*system")
    user_id: UUID | None = None
    severity: Literal["INFO", "WARN", "ERROR"]
    component: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1)
