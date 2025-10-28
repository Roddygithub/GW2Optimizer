"""Pydantic models for GW2 sync API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SyncStatus(BaseModel):
    """Current status of the GW2 data synchronization."""
    is_running: bool = Field(..., description="Whether a sync is currently running")
    last_run: Optional[datetime] = Field(None, description="When the last sync was started")
    last_success: Optional[datetime] = Field(None, description="When the last successful sync completed")
    next_run: Optional[datetime] = Field(None, description="When the next scheduled sync will run")
    error: Optional[str] = Field(None, description="Error message from the last sync, if any")


class SyncTask(BaseModel):
    """Response model for sync task operations."""
    message: str = Field(..., description="Status message")
    task_id: str = Field(..., description="ID of the sync task")
    status: str = Field(..., description="Current status of the task")
