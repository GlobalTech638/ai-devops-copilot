"""GitHub REST implementation for repository analysis."""

import base64
import os
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.services.github_adapter import GitHubFile

API_BASE = "https://api.github.com"
API_VERSION = "2026-03-10"


class GitHubApiError(RuntimeError):
    """Actionable GitHub API failure."""


class GitHubApiClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")

    def _get(self, path: str) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "ai-devops-copilot",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(f"{API_BASE}{path}", headers=headers, method="GET")
        try:
            with urlopen(request, timeout=20) as response:
                import json
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise GitHubApiError("GitHub repository, ref, or file was not found") from exc
            if exc.code == 401:
                raise GitHubApiError("GitHub authentication failed") from exc
            if exc.code == 403:
                raise GitHubApiError("GitHub access denied or rate limit reached") from exc
            raise GitHubApiError(f"GitHub API request failed ({exc.code})") from exc

    def list_tree(self, repository: str, ref: str) -> list[dict]:
        owner, name = _split_repository(repository)
        encoded_ref = quote(ref, safe="")
        payload = self._get(f"/repos/{owner}/{name}/git/trees/{encoded_ref}?recursive=1")
        if payload.get("truncated"):
            raise GitHubApiError("Repository tree is too large for one recursive request")
        return payload.get("tree", [])

    def get_file(self, repository: str, path: str, ref: str) -> GitHubFile:
        owner, name = _split_repository(repository)
        encoded_path = quote(path, safe="/")
        encoded_ref = quote(ref, safe="")
        payload = self._get(f"/repos/{owner}/{name}/contents/{encoded_path}?ref={encoded_ref}")
        if payload.get("type") != "file":
            raise GitHubApiError(f"GitHub path is not a regular file: {path}")
        if payload.get("encoding") != "base64":
            raise GitHubApiError(f"Unsupported GitHub content encoding for: {path}")
        content = base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
        return GitHubFile(path=path, size=int(payload.get("size", len(content))), content=content)


def _split_repository(repository: str) -> tuple[str, str]:
    parts = repository.strip().strip("/").split("/")
    if len(parts) != 2 or not all(parts):
        raise GitHubApiError("Repository must use owner/name format")
    return parts[0], parts[1]
