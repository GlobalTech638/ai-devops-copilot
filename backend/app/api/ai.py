"""AI-assisted analysis endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.analyzer_factory import get_analyzer
from app.services.context_builder import RepositoryFile, build_context
from app.services.repository_analyzer import analyze_paths

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class AIAnalyzeRequest(BaseModel):
    paths: list[str] = Field(default_factory=list)
    files: list[dict[str, str]] = Field(default_factory=list)


@router.post("/repository")
def analyze_with_ai(request: AIAnalyzeRequest) -> dict:
    """Analyze bounded repository evidence with the configured analyzer."""
    raw_findings = [finding.__dict__ for finding in analyze_paths(request.paths)]
    context = build_context(
        [RepositoryFile(path=item["path"], content=item.get("content", "")) for item in request.files]
    )
    result = get_analyzer().analyze(context)
    return {"context_preview": context[:4000], "signals": raw_findings, **result.model_dump()}
