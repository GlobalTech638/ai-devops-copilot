"""Asynchronous analysis job endpoints."""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.models.jobs import AnalysisJob
from app.services.analysis_runner import run_analysis
from app.services.job_store import create_job, get_job

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


class CreateJobRequest(BaseModel):
    repository: str = Field(
        pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$",
        description="GitHub owner/repository",
    )
    ref: str = Field(
        default="main",
        min_length=1,
        max_length=255,
        pattern=r"^[A-Za-z0-9_./-]+$",
        description="Git branch, tag, or commit ref",
    )


@router.post("", response_model=AnalysisJob, status_code=202)
def create_analysis_job(request: CreateJobRequest, background_tasks: BackgroundTasks) -> AnalysisJob:
    """Create an analysis job and execute the GitHub scan after the response is queued."""
    job = create_job(request.repository, request.ref)
    background_tasks.add_task(run_analysis, job.id, job.repository, job.ref)
    return job


@router.get("/{job_id}", response_model=AnalysisJob)
def read_analysis_job(job_id: str) -> AnalysisJob:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return job
