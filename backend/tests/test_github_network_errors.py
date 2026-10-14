from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from app.services import github_api_client as client_module
from app.services.github_api_client import GitHubApiClient, GitHubApiError


def test_network_error_becomes_actionable_github_error(monkeypatch):
    client = GitHubApiClient(token="test-token")

    def fail_urlopen(request, timeout):
        raise URLError("private network detail")

    monkeypatch.setattr(client_module, "urlopen", fail_urlopen)
    with pytest.raises(GitHubApiError, match="temporarily unreachable") as error:
        client._request("GET", "/repos/owner/repo")

    assert "private network detail" not in str(error.value)


def test_timeout_becomes_actionable_github_error(monkeypatch):
    client = GitHubApiClient(token="test-token")

    def fail_urlopen(request, timeout):
        raise TimeoutError("socket internals")

    monkeypatch.setattr(client_module, "urlopen", fail_urlopen)
    with pytest.raises(GitHubApiError, match="temporarily unreachable"):
        client._request("GET", "/repos/owner/repo")


def test_http_error_body_is_not_exposed(monkeypatch):
    client = GitHubApiClient(token="test-token")

    def fail_urlopen(request, timeout):
        raise HTTPError(request.full_url, 403, "Forbidden", {}, BytesIO(b"private error detail"))

    monkeypatch.setattr(client_module, "urlopen", fail_urlopen)
    with pytest.raises(GitHubApiError) as error:
        client._request("GET", "/repos/owner/repo")

    assert "private error detail" not in str(error.value)
