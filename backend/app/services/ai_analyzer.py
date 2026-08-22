"""AI analysis boundary.

The service intentionally separates prompt/context construction from the model
provider. This lets us add an LLM provider without coupling the API to one vendor.
"""

from app.models.findings import AnalysisResult, Finding


SYSTEM_PROMPT = """You are an expert software engineering reviewer.
Analyze repository evidence conservatively. Never invent evidence.
Return structured findings with category, severity, title, evidence,
recommendation, and confidence. Prioritize actionable risks."""


def build_analysis_context(paths: list[str], findings: list[dict]) -> str:
    """Build a compact, deterministic context payload for an AI provider."""
    return (
        "Repository paths:\n"
        + "\n".join(f"- {path}" for path in paths)
        + "\n\nExisting deterministic findings:\n"
        + "\n".join(f"- {item}" for item in findings)
    )


def fallback_analysis(findings: list[dict]) -> AnalysisResult:
    """Return a valid result when no AI provider is configured yet."""
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
