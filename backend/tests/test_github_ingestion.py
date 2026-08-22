from app.services.github_ingestion import select_files, should_ingest


def test_rejects_traversal():
    assert not should_ingest("../secrets.txt", 100)


def test_rejects_secrets_and_binary_files():
    assert not should_ingest(".env", 100)
    assert not should_ingest("assets/logo.png", 100)


def test_select_files_is_bounded():
    entries = [{"type": "blob", "path": f"src/file{i}.py", "size": 10} for i in range(100)]
    assert len(select_files(entries)) == 80
