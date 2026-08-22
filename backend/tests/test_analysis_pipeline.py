from app.services.analysis_pipeline import analyze_snapshot
from app.services.github_ingestion_service import RepositorySnapshot


def test_pipeline_builds_analysis_result():
    snapshot = RepositorySnapshot(
        repository="owner/repo",
        ref="main",
        files=[{"type": "blob", "path": "README.md", "size": 10}],
    )
    result = analyze_snapshot(snapshot, {"README.md": "# Example"})
    assert "summary" in result.model_dump()
