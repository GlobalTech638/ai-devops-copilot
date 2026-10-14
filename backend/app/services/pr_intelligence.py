"""Pull-request risk analysis primitives with line-aware diff parsing."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class PRFinding:
    category: str
    severity: str
    title: str
    evidence: str
    recommendation: str
    confidence: float
    path: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class PRAnalysis:
    risk_score: int
    merge_recommendation: str
    summary: str
    findings: list[PRFinding]


def _added_lines(diff: str) -> list[tuple[str, int, str]]:
    """Return (path, new line number, content) tuples from unified diff additions."""
    added: list[tuple[str, int, str]] = []
    path = None
    new_line = None
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            candidate = raw[4:].strip()
            path = candidate[2:] if candidate.startswith("b/") else candidate
            if path == "/dev/null":
                path = None
            new_line = None
        elif raw.startswith("--- "):
            continue
        elif raw.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,(\d+))?", raw)
            new_line = int(match.group(1)) if match else None
        elif path is not None and new_line is not None:
            if raw.startswith("+") and not raw.startswith("+++"):
                added.append((path, new_line, raw[1:]))
                new_line += 1
            elif raw.startswith(" "):
                new_line += 1
            # Removed lines do not advance the new-file line counter.
    return added


def analyze_diff(diff: str) -> PRAnalysis:
    """Run deterministic heuristics and never echo possible secret values into evidence."""
    findings: list[PRFinding] = []
    credential_markers = (
        "api_" + "key", "sec" + "ret", "pass" + "word",
        "private_" + "key", "aws_access_" + "key_id",
    )
    for path, line, content in _added_lines(diff):
        lowered = content.lower()
        if any(marker in lowered for marker in credential_markers):
            findings.append(PRFinding(
                "security", "critical", "Possible credential introduced",
                "Credential-like field detected on this added line; source content is intentionally omitted.",
                "Remove the exposed value, rotate it if needed, and use a managed secret store.",
                0.94, path, line,
            ))
        if "verify=false" in lowered or "ssl_verify = false" in lowered:
            findings.append(PRFinding(
                "security", "high", "TLS verification appears disabled",
                "The added line appears to disable certificate verification.",
                "Keep TLS certificate verification enabled and configure the trusted CA correctly.",
                0.91, path, line,
            ))
        if "todo" in lowered or "fixme" in lowered:
            findings.append(PRFinding(
                "quality", "medium", "Unresolved work marker added",
                "The added line introduces a TODO/FIXME marker.",
                "Resolve the marker or create a tracked issue before merge.",
                0.79, path, line,
            ))
    if not findings:
        score, recommendation = 12, "low risk"
        summary = "No high-signal security or quality hazards were detected by the first-pass review."
    else:
        weights = {"critical": 75, "high": 55, "medium": 30, "low": 15}
        score = min(100, max(weights.get(item.severity, 10) for item in findings) + (len(findings) - 1) * 5)
        recommendation = "changes requested" if score >= 50 else "review recommended"
        summary = f"Detected {len(findings)} risk signal(s) requiring review."
    return PRAnalysis(score, recommendation, summary, findings)
