"""Thread-safe in-memory job store for the MVP.

Replace with Redis/PostgreSQL for multi-process deployments. Updates use a lock
so concurrent background tasks and API reads cannot overwrite each other.
"""

from threading import RLock
from uuid import uuid4

from app.models.findings import AnalysisResult
from app.models.jobs import AnalysisJob, JobStatus

_JOBS: dict[str, AnalysisJob] = {}
_LOCK = RLock()


def create_job(repository: str, ref: str = "main") -> AnalysisJob:
    job = AnalysisJob(id=str(uuid4()), repository=repository, ref=ref)
    with _LOCK:
        _JOBS[job.id] = job
    return job


def get_job(job_id: str) -> AnalysisJob | None:
    with _LOCK:
        return _JOBS.get(job_id)


def update_job(job_id: str, status: JobStatus, progress: int) -> AnalysisJob:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            raise KeyError(f"Unknown analysis job: {job_id}")
        if job.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            return job
        updated = job.model_copy(update={"status": status, "progress": progress, "error": None})
        _JOBS[job_id] = updated
        return updated


def save_result(job_id: str, result: AnalysisResult) -> AnalysisJob:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            raise KeyError(f"Unknown analysis job: {job_id}")
        if job.status == JobStatus.FAILED:
            return job
        updated = job.model_copy(update={"result": result, "status": JobStatus.COMPLETED, "progress": 100, "error": None})
        _JOBS[job_id] = updated
        return updated


def fail_job(job_id: str, error: str) -> AnalysisJob:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            raise KeyError(f"Unknown analysis job: {job_id}")
        if job.status == JobStatus.COMPLETED:
            return job
        # Keep API-facing error safe; detailed exception logging belongs in observability.
        updated = job.model_copy(update={"status": JobStatus.FAILED, "progress": 100, "error": _safe_error(error)})
        _JOBS[job_id] = updated
        return updated


def _safe_error(error: str) -> str:
    """Return a bounded error message without likely credential values."""
    import re

    value = str(error)
    value = re.sub(r"(?i)(token|password|secret|api[_-]?key)=?\s*[^\s,;]+", r"\1=[REDACTED]", value)
    value = re.sub(r"gh[pousr]_[A-Za-z0-9_]{20,}", "[REDACTED_GITHUB_TOKEN]", value)
    value = re.sub(r"sk-[A-Za-z0-9_-]{16,}", "[REDACTED_API_KEY]", value)
    return value[:300]
