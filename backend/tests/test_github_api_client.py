import pytest

from app.services.github_api_client import GitHubApiClient, GitHubApiError, _split_repository


def test_split_repository_requires_owner_and_name():
    assert _split_repository("octo/project") == ("octo", "project")
    with pytest.raises(GitHubApiError):
        _split_repository("project")


def test_client_uses_explicit_token():
    client = GitHubApiClient(token="secret")
    assert client.token == "secret"
