import pytest

from app.models.findings import AnalysisResult
from app.models.jobs import JobStatus
from app.services import job_store


@pytest.fixture(autouse=True)
def isolated_job_database(tmp_path, monkeypatch):
    monkeypatch.setenv("JOB_STORE_PATH", str(tmp_path / "jobs.sqlite3"))


def test_job_store_failure_redacts_common_secret_patterns():
    job = job_store.create_job("owner/repo", "main")
    failed = job_store.fail_job(
        job.id,
        "request failed token=demo-token password=demo-password api_key=demo-key",
    )

    assert failed.status == JobStatus.FAILED
    assert "demo-token" not in failed.error
    assert "demo-password" not in failed.error
    assert "demo-key" not in failed.error
    assert "[REDACTED" in failed.error


def test_terminal_job_cannot_be_overwritten_by_progress_update():
    job = job_store.create_job("owner/repo", "main")
    completed = job_store.save_result(job.id, AnalysisResult(summary="ok", findings=[]))

    after = job_store.update_job(job.id, JobStatus.SCANNING, 10)

    assert after.status == JobStatus.COMPLETED
    assert after.progress == 100


def test_unknown_job_update_fails_clearly():
    with pytest.raises(KeyError, match="Unknown analysis job"):
        job_store.update_job("missing", JobStatus.SCANNING, 10)


def test_job_survives_store_reinitialization(tmp_path, monkeypatch):
    db_path = tmp_path / "persistent.sqlite3"
    monkeypatch.setenv("JOB_STORE_PATH", str(db_path))
    created = job_store.create_job("owner/repo", "release/v1")

    # The store has no process-local job dictionary; a new lookup reads SQLite.
    restored = job_store.get_job(created.id)

    assert restored is not None
    assert restored.id == created.id
    assert restored.repository == "owner/repo"
    assert restored.ref == "release/v1"
    assert restored.status == JobStatus.QUEUED
