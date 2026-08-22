from app.models.jobs import JobStatus
from app.services.job_store import create_job, get_job, update_job


def test_job_lifecycle_store():
    job = create_job("GlobalTech638/ai-devops-copilot", "develop")
    assert job.status == JobStatus.QUEUED
    assert get_job(job.id) == job

    updated = update_job(job.id, JobStatus.SCANNING, 25)
    assert updated.status == JobStatus.SCANNING
    assert updated.progress == 25
