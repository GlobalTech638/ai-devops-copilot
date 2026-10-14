"""SQLite-backed persistent job store for the single-node MVP.

Set JOB_STORE_PATH to a durable database file. The /tmp default is convenient
for local development only; production deployments must mount persistent storage.
For multi-instance deployments, use a managed database and durable queue.
"""

from contextlib import closing
import os
import re
import sqlite3
from pathlib import Path
from threading import RLock
from uuid import uuid4

from app.models.findings import AnalysisResult
from app.models.jobs import AnalysisJob, JobStatus

_LOCK = RLock()
_DEFAULT_DB_PATH = "/tmp/ai-devops-copilot-jobs.sqlite3"


def _connect() -> sqlite3.Connection:
    path = os.getenv("JOB_STORE_PATH", _DEFAULT_DB_PATH)
    if path != ":memory:":
        Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.execute("PRAGMA busy_timeout = 10000")
    if path != ":memory:":
        connection.execute("PRAGMA journal_mode = WAL")
    with connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS analysis_jobs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
    return connection


def _write(job: AnalysisJob) -> None:
    with closing(_connect()) as connection:
        with connection:
            connection.execute(
                "INSERT INTO analysis_jobs (id, payload) VALUES (?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload",
                (job.id, job.model_dump_json()),
            )


def create_job(repository: str, ref: str = "main") -> AnalysisJob:
    job = AnalysisJob(id=str(uuid4()), repository=repository, ref=ref)
    with _LOCK:
        _write(job)
    return job


def get_job(job_id: str) -> AnalysisJob | None:
    with _LOCK, closing(_connect()) as connection:
        row = connection.execute(
            "SELECT payload FROM analysis_jobs WHERE id = ?", (job_id,)
        ).fetchone()
    return AnalysisJob.model_validate_json(row[0]) if row else None


def update_job(job_id: str, status: JobStatus, progress: int) -> AnalysisJob:
    with _LOCK:
        job = get_job(job_id)
        if job is None:
            raise KeyError(f"Unknown analysis job: {job_id}")
        if job.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            return job
        updated = job.model_copy(update={"status": status, "progress": progress, "error": None})
        _write(updated)
        return updated


def save_result(job_id: str, result: AnalysisResult) -> AnalysisJob:
    with _LOCK:
        job = get_job(job_id)
        if job is None:
            raise KeyError(f"Unknown analysis job: {job_id}")
        if job.status == JobStatus.FAILED:
            return job
        updated = job.model_copy(update={
            "result": result, "status": JobStatus.COMPLETED, "progress": 100, "error": None
        })
        _write(updated)
        return updated


def fail_job(job_id: str, error: str) -> AnalysisJob:
    with _LOCK:
        job = get_job(job_id)
        if job is None:
            raise KeyError(f"Unknown analysis job: {job_id}")
        if job.status == JobStatus.COMPLETED:
            return job
        updated = job.model_copy(update={
            "status": JobStatus.FAILED, "progress": 100, "error": _safe_error(error)
        })
        _write(updated)
        return updated


def _safe_error(error: str) -> str:
    """Return a bounded error message without likely credential values."""
    value = str(error)
    value = re.sub(r"(?i)(token|password|secret|api[_-]?key)=?\s*[^\s,;]+", r"\1=[REDACTED]", value)
    value = re.sub(r"gh[pousr]_[A-Za-z0-9_]{20,}", "[REDACTED_GITHUB_TOKEN]", value)
    value = re.sub(r"sk-[A-Za-z0-9_-]{16,}", "[REDACTED_API_KEY]", value)
    return value[:300]


def recover_interrupted_jobs() -> int:
    """Mark non-terminal jobs as failed after an application restart.

    Background tasks are process-local in this MVP. A job left queued or in a
    processing state cannot safely resume without a durable task queue.
    Returns the number of jobs recovered.
    """
    recovered = 0
    with _LOCK, closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT payload FROM analysis_jobs"
        ).fetchall()
        for (payload,) in rows:
            job = AnalysisJob.model_validate_json(payload)
            if job.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
                continue
            updated = job.model_copy(update={
                "status": JobStatus.FAILED,
                "progress": 100,
                "error": "Analysis was interrupted by an application restart. Please submit a new job.",
            })
            connection.execute(
                "UPDATE analysis_jobs SET payload = ? WHERE id = ?",
                (updated.model_dump_json(), updated.id),
            )
            recovered += 1
        connection.commit()
    return recovered
