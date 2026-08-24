"""Pull-request intelligence API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.github_api_client import GitHubApiError, GitHubApiClient
from app.services.pr_intelligence import PRAnalysis, analyze_diff

router = APIRouter(prefix="/api/v1/pull-requests", tags=["pull-requests"])


class PRReviewRequest(BaseModel):
    repository: str = Field(min_length=1)
    pull_request: int = Field(gt=0)


@router.post("/review", response_model=PRAnalysis)
def review_pull_request(request: PRReviewRequest) -> PRAnalysis:
    github = GitHubApiClient()
    try:
        payload = github._get(f"/repos/{request.repository}/pulls/{request.pull_request}")
        diff_url = payload.get("diff_url")
        if not diff_url:
            raise HTTPException(status_code=422, detail="GitHub did not return a pull request diff URL")
        diff = github.fetch_diff_url(diff_url)
        return analyze_diff(diff)
    except GitHubApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
