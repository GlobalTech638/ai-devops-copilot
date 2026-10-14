"""Pull-request intelligence API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.github_api_client import GitHubApiError, GitHubApiClient
from app.services.pr_intelligence import PRAnalysis, analyze_diff
from app.services.review_plan import build_review_plan
from app.services.review_publisher import ReviewPublishError, publish_review

router = APIRouter(prefix="/api/v1/pull-requests", tags=["pull-requests"])


class PRReviewRequest(BaseModel):
    repository: str = Field(pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
    pull_request: int = Field(gt=0)


class PRPublishRequest(PRReviewRequest):
    # Live publishing requires an explicit head commit SHA. Dry-run remains the default.
    commit_id: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{40}$")
    dry_run: bool = True


@router.post("/review", response_model=PRAnalysis)
def review_pull_request(request: PRReviewRequest) -> PRAnalysis:
    try:
        diff = GitHubApiClient().get_pull_request_patch(request.repository, request.pull_request)
        return analyze_diff(diff)
    except GitHubApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/review/plan")
def plan_pull_request_review(request: PRReviewRequest) -> dict:
    """Analyze a PR and return a review plan without posting to GitHub."""
    try:
        analysis = analyze_diff(
            GitHubApiClient().get_pull_request_patch(request.repository, request.pull_request)
        )
        plan = build_review_plan(analysis.findings)
        return {
            "repository": request.repository,
            "pull_request": request.pull_request,
            "risk_score": analysis.risk_score,
            "merge_recommendation": analysis.merge_recommendation,
            "summary": analysis.summary,
            "review_action": plan.recommendation,
            "inline_comment_count": len(plan.comments),
            "comments": [
                {
                    "path": comment.path,
                    "line": comment.line,
                    "side": comment.side,
                    "severity": comment.severity,
                    "body": comment.body,
                    "confidence": comment.confidence,
                }
                for comment in plan.comments
            ],
            "dry_run": True,
        }
    except GitHubApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/review/publish")
def publish_pull_request_review(request: PRPublishRequest) -> dict:
    """Build and publish a PR review; live mutation requires explicit opt-in and a commit SHA."""
    if not request.dry_run and not request.commit_id:
        raise HTTPException(
            status_code=400,
            detail="commit_id (the pull request head SHA) is required when dry_run=false",
        )
    try:
        diff = GitHubApiClient().get_pull_request_patch(request.repository, request.pull_request)
        analysis = analyze_diff(diff)
        plan = build_review_plan(analysis.findings)
        result = publish_review(
            request.repository,
            request.pull_request,
            plan,
            commit_id=request.commit_id,
            dry_run=request.dry_run,
        )
        return {
            "repository": request.repository,
            "pull_request": request.pull_request,
            "risk_score": analysis.risk_score,
            "merge_recommendation": analysis.merge_recommendation,
            "summary": analysis.summary,
            **result,
        }
    except (GitHubApiError, ReviewPublishError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
