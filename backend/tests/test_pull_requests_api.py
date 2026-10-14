from fastapi.testclient import TestClient

from app.main import app
from app.api import pull_requests


class FakeGitHubClient:
    def get_pull_request_patch(self, repository: str, pull_request: int) -> str:
        return """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -0,0 +1 @@
+password = "do-not-leak-this"
"""


def test_review_plan_is_dry_run_and_redacts_credentials(monkeypatch):
    monkeypatch.setattr(pull_requests, "GitHubApiClient", FakeGitHubClient)
    client = TestClient(app)

    response = client.post(
        "/api/v1/pull-requests/review/plan",
        json={"repository": "owner/repo", "pull_request": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert payload["inline_comment_count"] == 1
    assert payload["comments"][0]["path"] == "app.py"
    assert payload["comments"][0]["line"] == 1
    assert "do-not-leak-this" not in payload["comments"][0]["body"]


def test_live_publish_without_commit_sha_is_rejected_before_github_call(monkeypatch):
    def forbidden_client():
        raise AssertionError("GitHub client must not be called")

    monkeypatch.setattr(pull_requests, "GitHubApiClient", forbidden_client)
    client = TestClient(app)

    response = client.post(
        "/api/v1/pull-requests/review/publish",
        json={
            "repository": "owner/repo",
            "pull_request": 3,
            "dry_run": False,
        },
    )

    assert response.status_code == 400
    assert "commit_id" in response.json()["detail"]


def test_publish_route_defaults_to_dry_run(monkeypatch):
    monkeypatch.setattr(pull_requests, "GitHubApiClient", FakeGitHubClient)
    client = TestClient(app)

    response = client.post(
        "/api/v1/pull-requests/review/publish",
        json={"repository": "owner/repo", "pull_request": 3},
    )

    assert response.status_code == 200
    assert response.json()["dry_run"] is True


def test_invalid_repository_identifier_is_rejected_by_request_validation(monkeypatch):
    def forbidden_client():
        raise AssertionError("GitHub client must not be called")

    monkeypatch.setattr(pull_requests, "GitHubApiClient", forbidden_client)
    response = TestClient(app).post(
        "/api/v1/pull-requests/review/plan",
        json={"repository": "owner/repo/extra", "pull_request": 3},
    )

    assert response.status_code == 422


def test_invalid_commit_sha_is_rejected_by_request_validation():
    response = TestClient(app).post(
        "/api/v1/pull-requests/review/publish",
        json={
            "repository": "owner/repo",
            "pull_request": 3,
            "commit_id": "not-a-real-sha",
            "dry_run": False,
        },
    )

    assert response.status_code == 422
