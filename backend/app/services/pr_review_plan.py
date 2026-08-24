"""Convert PR analysis findings into review-ready, non-mutating actions."""

from dataclasses import dataclass

from app.services.pr_intelligence import PRAnalysis


@dataclass(frozen=True)
class ReviewComment:
    path: str
    line: int
    side: str
    severity: str
    title: str
    body: str
    confidence: float


@dataclass(frozen=True)
class ReviewPlan:
    recommendation: str
    risk_score: int
    summary: str
    comments: list[ReviewComment]


def build_review_plan(analysis: PRAnalysis, changed_files: dict[str, str]) -> ReviewPlan:
    """Map findings to changed-file lines without mutating GitHub.

    Findings from the current heuristic analyzer do not yet carry source
    locations, so this function uses conservative keyword matching against
    added lines. Unmatched findings remain in the summary and are not posted
    as inline comments.
    """
    comments: list[ReviewComment] = []
    for finding in analysis.findings:
        needle = _needle_for(finding.title)
        if not needle:
            continue
        for path, patch in changed_files.items():
            for line_no, line in _added_lines(patch):
                if needle in line.lower():
                    comments.append(ReviewComment(
                        path=path,
                        line=line_no,
                        side="RIGHT",
                        severity=finding.severity,
                        title=finding.title,
                        body=f"**{finding.severity.upper()} — {finding.title}**\n\n{finding.evidence}\n\n**Recommendation:** {finding.recommendation}",
                        confidence=finding.confidence,
                    ))
                    break
            if any(comment.title == finding.title for comment in comments):
                break
    return ReviewPlan(analysis.merge_recommendation, analysis.risk_score, analysis.summary, comments)


def _added_lines(patch: str):
    new_line = 0
    for raw in patch.splitlines():
        if raw.startswith("@@"):
            try:
                new_line = int(raw.split("+")[1].split(",")[0])
            except (IndexError, ValueError):
                new_line = 0
            continue
        if raw.startswith("+++"):
            continue
        if raw.startswith("+"):
            if new_line:
                yield new_line, raw[1:]
            new_line += 1
        elif raw.startswith("-"):
            continue
        else:
            if new_line:
                new_line += 1


def _needle_for(title: str) -> str | None:
    title = title.lower()
    if "credential" in title:
        return "="
    if "tls" in title:
        return "verify"
    if "work marker" in title:
        return "todo"
    return None
