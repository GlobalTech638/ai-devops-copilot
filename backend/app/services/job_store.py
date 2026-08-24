"""Small in-memory job store for the MVP.

This is intentionally replaceable by Redis/PostgreSQL once background workers
are introduced. The API contract remains stable.
"""

from uuid import uuid4

from app.models.findings import AnalysisResult
from app.models.jobs import AnalysisJob, JobStatus

_JOBS: dict[str, AnalysisJob] = {}


def create_job(repository: str, ref: str = "main") -> AnalysisJob:
    job = AnalysisJob(id=str(uuid4()), repository=repository, ref=ref)
    _JOBS[job.id] = job
    return job


def get_job(job_id: str) -> AnalysisJob | None:
    return _JOBS.get(job_id)


def update_job(job_id: str, status: JobStatus, progress: int) -> AnalysisJob:
    job = _JOBS[job_id]
    updated = job.model_copy(update={"status": status, "progress": progress})
    _JOBS[job_id] = updated
    return updated


def save_result(job_id: str, result: AnalysisResult) -> AnalysisJob:
    job = _JOBS[job_id]
    updated = job.model_copy(update={"result": result, "status": JobStatus.COMPLETED, "progress": 100, "error": None})
    _JOBS[job_id] = updated
    return updated


def fail_job(job_id: str, error: str) -> AnalysisJob:
    job = _JOBS[job_id]
    updated = job.model_copy(update={"status": JobStatus.FAILED, "progress": 100, "error": error[:500]})
    _JOBS[job_id] = updated
    return updated
