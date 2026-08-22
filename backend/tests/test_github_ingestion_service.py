from app.services.github_ingestion_service import build_snapshot


def test_snapshot_is_bounded_and_identifies_repo():
    entries = [{"type": "blob", "path": "src/app.py", "size": 100}]
    snapshot = build_snapshot("GlobalTech638/ai-devops-copilot", "develop", entries)
    assert snapshot.repository == "GlobalTech638/ai-devops-copilot"
    assert snapshot.ref == "develop"
    assert snapshot.files == entries
