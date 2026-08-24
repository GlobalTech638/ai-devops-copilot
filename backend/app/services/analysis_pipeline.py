"""Orchestration boundary for repository analysis."""

from app.models.findings import AnalysisResult
from app.services.ai_analyzer import baseline_analysis
from app.services.context_builder import RepositoryFile, build_context
from app.services.github_ingestion import IngestedFile


def analyze_snapshot(files: list[IngestedFile]) -> AnalysisResult:
    """Build bounded context from canonical GitHub ingestion and analyze it."""
    context = build_context([
        RepositoryFile(path=file.path, content=file.content)
        for file in files
    ])
    return baseline_analysis(context)
