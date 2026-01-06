"""
Common schemas used across API endpoints.
"""

from typing import List, TypeVar, Generic
from uuid import UUID
from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str = Field(..., example="Operation completed successfully")


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str = Field(..., example="Resource not found")


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int = Field(..., description="Total number of items matching query")
    limit: int = Field(..., description="Maximum items per page")
    offset: int = Field(..., description="Number of items skipped")

    class Config:
        from_attributes = True
