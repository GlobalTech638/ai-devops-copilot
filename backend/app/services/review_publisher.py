"""Publish an approved ReviewPlan to GitHub."""

from app.services.github_api_client import GitHubApiClient, GitHubApiError
from app.services.review_plan import ReviewPlan


class ReviewPublishError(RuntimeError):
    """Review could not be safely published."""


def publish_review(
    repository: str,
    pull_request: int,
    plan: ReviewPlan,
    commit_id: str | None = None,
    dry_run: bool = True,
) -> dict:
    """Publish a review, defaulting to dry-run to prevent accidental mutation."""
    payload = {
        "action": plan.recommendation,
        "summary": f"AI DevOps Copilot found {len(plan.comments)} inline finding(s).",
        "comments": [
            {
                "path": comment.path,
                "line": comment.line,
                "side": comment.side,
                "severity": comment.severity,
                "body": comment.body,
            }
            for comment in plan.comments
        ],
    }
    if dry_run:
        return {"dry_run": True, "payload": payload}

    if plan.recommendation not in {"COMMENT", "REQUEST_CHANGES"}:
        raise ReviewPublishError("Unsupported review action")

    client = GitHubApiClient()
    try:
        result = client.add_pull_request_review(
            repository,
            pull_request,
            action=plan.recommendation,
            review=payload["summary"],
            file_comments=plan.comments,
            commit_id=commit_id,
        )
    except GitHubApiError as exc:
        raise ReviewPublishError(str(exc)) from exc
    return {"dry_run": False, "payload": payload, "github": result}
