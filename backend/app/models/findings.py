"""Structured finding models used across deterministic and AI analysis."""

from pydantic import BaseModel, Field


class Finding(BaseModel):
    category: str
    severity: str = Field(pattern="^(info|low|medium|high|critical)$")
    title: str
    evidence: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)


class AnalysisResult(BaseModel):
    summary: str
    findings: list[Finding]
