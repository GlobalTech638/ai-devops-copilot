"""Project health API."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.health_score import calculate_health_score

router = APIRouter(prefix="/api/v1/health", tags=["health"])


class HealthRequest(BaseModel):
    findings: list[dict[str, str]] = Field(default_factory=list)


@router.post("/score")
def health_score(request: HealthRequest) -> dict[str, int | str]:
    """Return an explainable project health score."""
    result = calculate_health_score(request.findings)
    return {"score": result.score, "grade": result.grade}
