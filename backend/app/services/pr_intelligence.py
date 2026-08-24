"""Pull-request risk analysis primitives."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PRFinding:
    category: str
    severity: str
    title: str
    evidence: str
    recommendation: str
    confidence: float


@dataclass(frozen=True)
class PRAnalysis:
    risk_score: int
    merge_recommendation: str
    summary: str
    findings: list[PRFinding]


def analyze_diff(diff: str) -> PRAnalysis:
    """Run deterministic first-pass PR heuristics before an AI review.

    The heuristic layer is intentionally conservative and bounded. AI review
    can be added behind this stable result contract without changing callers.
    """
    findings: list[PRFinding] = []
    added = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    lowered = "\n".join(added).lower()

    secret_markers = ("api_key=", "secret=", "password=", "private_key", "aws_access_key_id")
    if any(marker in lowered for marker in secret_markers):
        findings.append(PRFinding(
            category="security", severity="critical", title="Possible credential introduced",
            evidence="Added lines contain a credential-like assignment.",
            recommendation="Remove the secret, rotate it if exposed, and use a managed secret store.", confidence=0.94,
        ))

    if "verify=false" in lowered or "ssl_verify = false" in lowered:
        findings.append(PRFinding(
            category="security", severity="high", title="TLS verification appears disabled",
            evidence="The diff contains a setting that disables certificate verification.",
            recommendation="Keep TLS certificate verification enabled and configure the trusted CA correctly.", confidence=0.91,
        ))

    if "todo" in lowered or "fixme" in lowered:
        findings.append(PRFinding(
            category="quality", severity="medium", title="Unresolved work marker added",
            evidence="The change introduces TODO/FIXME markers.",
            recommendation="Resolve the marker or create a tracked issue before merge.", confidence=0.79,
        ))

    if not findings:
        score = 12
        recommendation = "low risk"
        summary = "No high-signal security or quality hazards were detected by the first-pass review."
    else:
        weights = {"critical": 75, "high": 55, "medium": 30, "low": 15}
        score = min(100, max(weights.get(item.severity, 10) for item in findings) + (len(findings) - 1) * 5)
        recommendation = "changes requested" if score >= 50 else "review recommended"
        summary = f"Detected {len(findings)} risk signal(s) requiring review."

    return PRAnalysis(score, recommendation, summary, findings)
