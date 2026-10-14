from app.models.findings import AnalysisResult
from app.services.analysis_pipeline import analyze_snapshot
from app.services.github_ingestion import IngestedFile


class FakeAnalyzer:
    def analyze(self, context: str) -> AnalysisResult:
        assert "FILE CONTENT" in context
        assert "README.md" in context
        return AnalysisResult(summary="ok", findings=[])


def test_pipeline_builds_bounded_context_and_analysis_result(monkeypatch):
    monkeypatch.setattr("app.services.analysis_pipeline.get_analyzer", lambda: FakeAnalyzer())

    result = analyze_snapshot([
        IngestedFile(path="README.md", content="# FILE CONTENT"),
    ])

    assert result.summary == "ok"
    assert result.findings == []
