"""Convert PR findings into safe, review-ready GitHub actions."""

from dataclasses import dataclass

from app.services.pr_intelligence import PRFinding


@dataclass(frozen=True)
class ReviewComment:
    path: str
    line: int
    side: str
    severity: str
    body: str
    confidence: float


@dataclass(frozen=True)
class ReviewPlan:
    recommendation: str
    comments: list[ReviewComment]


def build_review_plan(findings: list[PRFinding]) -> ReviewPlan:
    """Create a review plan without mutating GitHub.

    Findings without an exact path/line are intentionally excluded from inline
    comments. They can still be surfaced as summary findings in the dashboard.
    """
    comments: list[ReviewComment] = []
    for finding in findings:
        path = getattr(finding, "path", None)
        line = getattr(finding, "line", None)
        if not path or not isinstance(line, int) or line < 1:
            continue
        body = (
            f"**{finding.severity.upper()} — {finding.title}**\n\n"
            f"{finding.evidence}\n\n"
            f"**Recommendation:** {finding.recommendation}\n\n"
            f"Confidence: {finding.confidence:.0%}"
        )
        comments.append(ReviewComment(path, line, "RIGHT", finding.severity, body, finding.confidence))

    recommendation = "REQUEST_CHANGES" if any(c.severity in {"critical", "high"} for c in comments) else "COMMENT"
    return ReviewPlan(recommendation=recommendation, comments=comments)
