from app.services.repository_analyzer import analyze_paths


def test_detects_python_and_missing_tests():
    findings = analyze_paths(["pyproject.toml", "app/main.py"])

    categories = {finding.category for finding in findings}
    assert "technology" in categories
    assert "testing" in categories
