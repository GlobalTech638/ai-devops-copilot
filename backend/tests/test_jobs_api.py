from fastapi.testclient import TestClient

from app.main import app
from app.api import jobs


client = TestClient(app)


def test_invalid_job_repository_is_rejected_before_queueing(monkeypatch):
    def forbidden_create_job(*args, **kwargs):
        raise AssertionError("job must not be created")

    monkeypatch.setattr(jobs, "create_job", forbidden_create_job)
    response = client.post(
        "/api/v1/jobs",
        json={"repository": "owner/repo/extra", "ref": "main"},
    )
    assert response.status_code == 422


def test_invalid_job_ref_is_rejected_before_queueing(monkeypatch):
    def forbidden_create_job(*args, **kwargs):
        raise AssertionError("job must not be created")

    monkeypatch.setattr(jobs, "create_job", forbidden_create_job)
    response = client.post(
        "/api/v1/jobs",
        json={"repository": "owner/repo", "ref": "../secrets"},
    )
    assert response.status_code == 422


def test_missing_job_returns_404():
    response = client.get("/api/v1/jobs/not-a-real-job")
    assert response.status_code == 404


def test_health_endpoint_smoke_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
