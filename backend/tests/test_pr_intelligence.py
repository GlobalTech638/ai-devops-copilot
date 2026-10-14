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
    assert "intentionally omitted" in credential.evidence

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


def test_credential_evidence_never_echoes_source_values():
    diff = """diff --git a/.env b/.env
--- a/.env
+++ b/.env
@@ -0,0 +1,2 @@
+private_key = "PRIVATE-MATERIAL"
+AWS_ACCESS_KEY_ID="AKIA-EXAMPLE-SECRET"
"""
    analysis = analyze_diff(diff)
    assert len(analysis.findings) == 2
    evidence = " ".join(item.evidence for item in analysis.findings)
    assert "PRIVATE-MATERIAL" not in evidence
    assert "AKIA-EXAMPLE-SECRET" not in evidence


def test_removed_lines_do_not_advance_new_file_line_number():
    diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,3 +1,3 @@
 first = True
-old_password = "removed"
+password = "new-value"
 last = True
"""
    added = _added_lines(diff)
    assert ("app.py", 2, 'password = "new-value"') in added
    analysis = analyze_diff(diff)
    assert analysis.findings[0].line == 2
    assert "new-value" not in analysis.findings[0].evidence
