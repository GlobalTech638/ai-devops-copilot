from app.services.context_builder import RepositoryFile, build_context


def test_context_builder_excludes_dependency_directories():
    context = build_context([
        RepositoryFile("src/main.py", "print('ok')"),
        RepositoryFile("node_modules/pkg/index.js", "ignored"),
    ])
    assert "src/main.py" in context
    assert "node_modules/pkg/index.js" not in context
