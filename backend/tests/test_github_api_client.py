import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from app.services import github_api_client as client_module
from app.services.github_api_client import GitHubApiClient, GitHubApiError, _split_repository


def test_split_repository_requires_owner_and_name():
    assert _split_repository("octo/project") == ("octo", "project")
    with pytest.raises(GitHubApiError):
        _split_repository("project")
    with pytest.raises(GitHubApiError):
        _split_repository("owner/repo/extra")


def test_client_uses_explicit_token():
    client = GitHubApiClient(token="test-token")
    assert client.token == "test-token"


def test_live_inline_review_requires_head_sha_before_network_call(monkeypatch):
    client = GitHubApiClient(token="test-token")

    def forbidden_urlopen(*args, **kwargs):
        raise AssertionError("network must not be called")

    monkeypatch.setattr(client_module, "urlopen", forbidden_urlopen)
    comment = type("Comment", (), {"path": "app.py", "line": 3, "side": "RIGHT", "body": "check"})()
    with pytest.raises(GitHubApiError, match="commit_id"):
        client.add_pull_request_review(
            "owner/repo", 7, action="COMMENT", review="review summary",
            file_comments=[comment],
        )


def test_live_review_requires_token(monkeypatch):
    client = GitHubApiClient(token=None)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(GitHubApiError, match="GITHUB_TOKEN"):
        client.add_pull_request_review(
            "owner/repo", 7, action="COMMENT", review="review summary",
            file_comments=[],
        )


def test_review_request_sends_commit_sha_and_inline_comment(monkeypatch):
    client = GitHubApiClient(token="test-token")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"id": 123, "state": "submitted"}).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["body"] = json.loads(request.data.decode())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)
    comment = type("Comment", (), {"path": "app.py", "line": 3, "side": "RIGHT", "body": "review finding"})()
    result = client.add_pull_request_review(
        "owner/repo", 7, action="COMMENT", review="AI review",
        file_comments=[comment], commit_id="a" * 40,
    )

    assert result["id"] == 123
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/repos/owner/repo/pulls/7/reviews")
    assert captured["body"]["commit_id"] == "a" * 40
    assert captured["body"]["comments"] == [
        {"path": "app.py", "line": 3, "side": "RIGHT", "body": "review finding"}
    ]
    assert captured["timeout"] == 20


def test_github_http_error_is_mapped_to_safe_message(monkeypatch):
    client = GitHubApiClient(token="test-token")

    def fail_urlopen(request, timeout):
        raise HTTPError(request.full_url, 403, "Forbidden", {}, BytesIO(b"private error detail"))

    monkeypatch.setattr(client_module, "urlopen", fail_urlopen)
    with pytest.raises(GitHubApiError, match="access denied or rate limit"):
        client._request("GET", "/repos/owner/repo")
