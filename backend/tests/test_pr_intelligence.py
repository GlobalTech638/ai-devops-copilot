from app.services.pr_intelligence import _added_lines, analyze_diff
from app.services.review_plan import build_review_plan


SAMPLE_DIFF = """diff --git a/app/config.py b/app/config.py
index 1111111..2222222 100644
--- a/app/config.py
+++ b/app/config.py
@@ -1,2 +1,3 @@
 import os
+password = "dont-print-this"
+requests.get(url, verify=False)
"""


def test_added_lines_track_new_line_numbers():
    assert _added_lines(SAMPLE_DIFF) == [
        ("app/config.py", 2, 'password = "dont-print-this"'),
        ("app/config.py", 3, "requests.get(url, verify=False)"),
    ]


def test_findings_have_exact_inline_locations_and_redact_credentials():
    analysis = analyze_diff(SAMPLE_DIFF)
    assert len(analysis.findings) == 2
    credential = analysis.findings[0]
    assert credential.path == "app/config.py"
    assert credential.line == 2
    assert "dont-print-this" not in credential.evidence
    assert "[REDACTED]" in credential.evidence

    tls = analysis.findings[1]
    assert tls.path == "app/config.py"
    assert tls.line == 3


def test_review_plan_contains_only_line_anchored_comments():
    analysis = analyze_diff(SAMPLE_DIFF)
    plan = build_review_plan(analysis.findings)
    assert plan.recommendation == "REQUEST_CHANGES"
    assert [(comment.path, comment.line) for comment in plan.comments] == [
        ("app/config.py", 2),
        ("app/config.py", 3),
    ]
