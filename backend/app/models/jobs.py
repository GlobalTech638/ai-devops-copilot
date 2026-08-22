"""Analysis job state models."""

from enum import Enum
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    SCANNING = "scanning"
    INDEXING = "indexing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisJob(BaseModel):
    id: str
    repository: str
    ref: str = "main"
    status: JobStatus = JobStatus.QUEUED
    progress: int = Field(default=0, ge=0, le=100)
    error: str | None = None
