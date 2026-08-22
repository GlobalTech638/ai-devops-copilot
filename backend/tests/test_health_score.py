from app.services.health_score import calculate_health_score


def test_clean_project_gets_a():
    result = calculate_health_score([])
    assert result.score == 100
    assert result.grade == "A"


def test_medium_finding_reduces_score():
    result = calculate_health_score([{"severity": "medium"}])
    assert result.score == 90
    assert result.grade == "A"
