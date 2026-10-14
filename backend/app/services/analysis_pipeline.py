"""Orchestration boundary for repository analysis."""

from app.models.findings import AnalysisResult
from app.services.analyzer_factory import get_analyzer
from app.services.context_builder import RepositoryFile, build_context
from app.services.github_ingestion import IngestedFile


def analyze_snapshot(files: list[IngestedFile]) -> AnalysisResult:
    """Build bounded context from ingested files and use the configured analyzer."""
    context = build_context([
        RepositoryFile(path=file.path, content=file.content)
        for file in files
    ])
    return get_analyzer().analyze(context)
