"""Orchestration boundary for repository analysis."""

from app.models.findings import AnalysisResult
from app.services.ai_analyzer import baseline_analysis
from app.services.context_builder import RepositoryFile, build_context
from app.services.github_ingestion_service import RepositorySnapshot


def analyze_snapshot(snapshot: RepositorySnapshot, contents: dict[str, str]) -> AnalysisResult:
    """Build bounded context and run the configured analysis implementation."""
    files = [
        RepositoryFile(path=entry["path"], content=contents.get(entry["path"], ""))
        for entry in snapshot.files
    ]
    context = build_context(files)
    return baseline_analysis(context)
