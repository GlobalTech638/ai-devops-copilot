"""AI-assisted analysis endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.ai_analyzer import build_analysis_context, fallback_analysis
from app.services.repository_analyzer import analyze_paths

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class AIAnalyzeRequest(BaseModel):
    paths: list[str] = Field(default_factory=list)


@router.post("/repository")
def analyze_with_ai(request: AIAnalyzeRequest) -> dict:
    """Analyze repository evidence through the AI boundary.

    Until a model provider is configured, this returns a deterministic fallback.
    """
    raw_findings = [finding.__dict__ for finding in analyze_paths(request.paths)]
    context = build_analysis_context(request.paths, raw_findings)
    result = fallback_analysis(raw_findings)
    return {"context_preview": context, **result.model_dump()}
