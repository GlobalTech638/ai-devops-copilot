"""Project health scoring based on analyzer findings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthScore:
    score: int
    grade: str


def calculate_health_score(findings: list[dict[str, str]]) -> HealthScore:
    """Calculate a simple explainable score from finding severity."""
    penalties = {"critical": 30, "high": 20, "medium": 10, "low": 4, "info": 0}
    score = max(0, min(100, 100 - sum(penalties.get(f.get("severity", "info"), 0) for f in findings)))

    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    return HealthScore(score=score, grade=grade)
