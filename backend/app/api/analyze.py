"""Repository analysis HTTP endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.repository_analyzer import analyze_paths

router = APIRouter(prefix="/api/v1/analyze", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    paths: list[str] = Field(default_factory=list, description="Repository-relative file paths")


@router.post("/repository")
def analyze_repository(request: AnalyzeRequest) -> dict:
    """Analyze repository structure and return structured findings."""
    findings = analyze_paths(request.paths)
    return {
        "finding_count": len(findings),
        "findings": [finding.__dict__ for finding in findings],
    }
