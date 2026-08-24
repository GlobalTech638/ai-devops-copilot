"""GitHub REST implementation for repository and pull-request analysis."""

import base64
import json
import os
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.services.github_adapter import GitHubFile

API_BASE = "https://api.github.com"
API_VERSION = "2022-11-28"


class GitHubApiError(RuntimeError):
    """Actionable GitHub API failure."""


class GitHubApiClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")

    def _request(self, method: str, path: str, accept: str = "application/vnd.github+json", payload: dict | None = None) -> dict | str:
        headers = {
            "Accept": accept,
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "ai-devops-copilot",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        body = json.dumps(payload).encode() if payload is not None else None
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(f"{API_BASE}{path}", headers=headers, method=method, data=body)
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
                if accept == "application/vnd.github.v3.diff":
                    return raw
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            if exc.code == 404:
                raise GitHubApiError("GitHub repository, ref, file, or pull request was not found") from exc
            if exc.code == 401:
                raise GitHubApiError("GitHub authentication failed") from exc
            if exc.code == 403:
                raise GitHubApiError("GitHub access denied or rate limit reached") from exc
            if exc.code == 422:
                raise GitHubApiError("GitHub rejected the request") from exc
            raise GitHubApiError(f"GitHub API request failed ({exc.code})") from exc

    def list_tree(self, repository: str, ref: str) -> list[dict]:
        owner, name = _split_repository(repository)
        encoded_ref = quote(ref, safe="")
        payload = self._request("GET", f"/repos/{owner}/{name}/git/trees/{encoded_ref}?recursive=1")
        if not isinstance(payload, dict):
            raise GitHubApiError("Unexpected GitHub tree response")
        if payload.get("truncated"):
            raise GitHubApiError("Repository tree is too large for one recursive request")
        return payload.get("tree", [])

    def get_file(self, repository: str, path: str, ref: str) -> GitHubFile:
        owner, name = _split_repository(repository)
        encoded_path = quote(path, safe="/")
        encoded_ref = quote(ref, safe="")
        payload = self._request("GET", f"/repos/{owner}/{name}/contents/{encoded_path}?ref={encoded_ref}")
        if not isinstance(payload, dict) or payload.get("type") != "file":
            raise GitHubApiError(f"GitHub path is not a regular file: {path}")
        if payload.get("encoding") != "base64":
            raise GitHubApiError(f"Unsupported GitHub content encoding for: {path}")
        content = base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
        return GitHubFile(path=path, size=int(payload.get("size", len(content))), content=content)

    def get_pull_request_patch(self, repository: str, pull_request: int) -> str:
        owner, name = _split_repository(repository)
        if pull_request <= 0:
            raise GitHubApiError("Pull request number must be positive")
        patch = self._request("GET", f"/repos/{owner}/{name}/pulls/{pull_request}", accept="application/vnd.github.v3.diff")
        if not isinstance(patch, str):
            raise GitHubApiError("Unexpected GitHub pull-request diff response")
        if len(patch) > 2_000_000:
            raise GitHubApiError("Pull-request diff exceeds the analysis limit")
        return patch

    def add_pull_request_review(
        self,
        repository: str,
        pull_request: int,
        *,
        action: str,
        review: str,
        file_comments: list,
        commit_id: str | None = None,
    ) -> dict:
        owner, name = _split_repository(repository)
        if action not in {"COMMENT", "REQUEST_CHANGES", "APPROVE"}:
            raise GitHubApiError("Unsupported GitHub review action")
        if not self.token:
            raise GitHubApiError("GITHUB_TOKEN is required to publish a GitHub review")
        comments = []
        for item in file_comments:
            comments.append({
                "path": item.path,
                "line": item.line,
                "side": item.side,
                "body": item.body,
            })
        payload = {"body": review, "event": action, "comments": comments}
        if commit_id:
            payload["commit_id"] = commit_id
        result = self._request("POST", f"/repos/{owner}/{name}/pulls/{pull_request}/reviews", payload=payload)
        if not isinstance(result, dict):
            raise GitHubApiError("Unexpected GitHub review response")
        return result


def _split_repository(repository: str) -> tuple[str, str]:
    parts = repository.strip().strip("/").split("/")
    if len(parts) != 2 or not all(parts):
        raise GitHubApiError("Repository must use owner/name format")
    return parts[0], parts[1]
