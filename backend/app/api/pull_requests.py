"""Pull-request intelligence API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.github_api_client import GitHubApiError, GitHubApiClient
from app.services.pr_intelligence import PRAnalysis, analyze_diff
from app.services.review_plan import build_review_plan

router = APIRouter(prefix="/api/v1/pull-requests", tags=["pull-requests"])


class PRReviewRequest(BaseModel):
    repository: str = Field(min_length=1)
    pull_request: int = Field(gt=0)


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
