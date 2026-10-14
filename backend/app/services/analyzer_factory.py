"""Select the semantic analyzer available in the current environment."""

import os
import re

from app.models.findings import AnalysisResult
from app.services.ai_analyzer import AIAnalyzer, fallback_analysis
from app.services.openai_analyzer import OpenAIAnalyzer


class FallbackAnalyzer:
    """Provide a small deterministic scan when no model API key is configured."""

    def analyze(self, context: str) -> AnalysisResult:
        findings: list[dict[str, str]] = []
        rules = (
            (re.compile(r"\bTODO\b|\bFIXME\b", re.IGNORECASE), "medium", "Unresolved work marker", "Track or resolve this TODO/FIXME marker."),
            (re.compile(r"verify\s*=\s*False|ssl_verify\s*=\s*false", re.IGNORECASE), "high", "TLS verification may be disabled", "Keep certificate verification enabled."),
            (re.compile(r"\beval\s*\("), "high", "Dynamic evaluation detected", "Avoid eval on untrusted or externally controlled input."),
            (re.compile(r"""(?:password|api[_-]?key|secret)\s*=\s*['"].{4,}['"]""", re.IGNORECASE), "high", "Possible hard-coded secret", "Move secrets to a managed secret store and rotate exposed values."),
        )
        for line_number, line in enumerate(context.splitlines(), start=1):
            for pattern, severity, title, recommendation in rules:
                if pattern.search(line):
                    # Do not return source lines; they may contain credentials.
                    findings.append({
                        "category": "security" if "secret" in title.lower() or "TLS" in title else "quality",
                        "severity": severity,
                        "message": f"{title} detected in supplied context near line {line_number}. {recommendation}",
                    })
                    break
        return fallback_analysis(findings)


def get_analyzer() -> AIAnalyzer:
    """Prefer OpenAI when configured, otherwise use a safe local fallback."""
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIAnalyzer()
    return FallbackAnalyzer()
