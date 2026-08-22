"""Provider-neutral AI analysis contract.

The core application does not depend on one model vendor. A provider adapter can
implement ``AIAnalyzer`` and consume the bounded context produced by the context
builder. Until a provider is configured, deterministic evidence is returned.
"""

from typing import Protocol

from app.models.findings import AnalysisResult, Finding

SYSTEM_PROMPT = """You are an expert software engineering reviewer.
Analyze only supplied repository evidence. Never invent files, behavior, CVEs, or
vulnerabilities. Every finding must cite concrete evidence. Prioritize correctness,
security, reliability, maintainability, and testability. Return structured findings
with severity, confidence, evidence, and remediation."""


class AIAnalyzer(Protocol):
    def analyze(self, context: str) -> AnalysisResult:
        """Analyze bounded repository context."""


def fallback_analysis(findings: list[dict]) -> AnalysisResult:
    """Return useful structured findings when no external model is configured."""
    structured = [
        Finding(
            category=item.get("category", "engineering"),
            severity=item.get("severity", "info"),
            title=item.get("message", "Engineering signal"),
            evidence=item.get("message", "Detected by deterministic analysis."),
            recommendation="Review this signal and address it if applicable.",
            confidence=0.95,
        )
        for item in findings
    ]
    return AnalysisResult(
        summary=f"Generated {len(structured)} evidence-based engineering findings.",
        findings=structured,
    )
