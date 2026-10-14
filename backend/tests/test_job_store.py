import pytest

from app.models.jobs import JobStatus
from app.services import job_store


@pytest.fixture(autouse=True)
def clean_jobs():
    with job_store._LOCK:
        job_store._JOBS.clear()
    yield
    with job_store._LOCK:
        job_store._JOBS.clear()


def test_job_store_failure_redacts_common_secret_patterns():
    job = job_store.create_job("owner/repo", "main")
    failed = job_store.fail_job(
        job.id,
        "request failed token=ghp_abcdefghijklmnopqrstuvwxyz123456 password=hunter2 sk-abcdefghijklmnopqrstuvwxyz123456",
    )

    assert failed.status == JobStatus.FAILED
    assert "ghp_abcdefghijklmnopqrstuvwxyz123456" not in failed.error
    assert "hunter2" not in failed.error
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in failed.error
    assert "[REDACTED" in failed.error


def test_terminal_job_cannot_be_overwritten_by_progress_update():
    job = job_store.create_job("owner/repo", "main")
    completed = job_store.save_result(job.id, result=None)

    after = job_store.update_job(job.id, JobStatus.SCANNING, 10)

    assert after.status == JobStatus.COMPLETED
    assert after.progress == 100


def test_unknown_job_update_fails_clearly():
    with pytest.raises(KeyError, match="Unknown analysis job"):
        job_store.update_job("missing", JobStatus.SCANNING, 10)
