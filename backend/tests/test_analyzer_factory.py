from app.services.analyzer_factory import FallbackAnalyzer


def test_fallback_analyzer_detects_basic_risks_without_echoing_source():
    result = FallbackAnalyzer().analyze(
        'README.md\nTODO: finish this\npassword = "secret-value-123"\nrequests.get(url, verify=False)'
    )

    assert len(result.findings) == 3
    assert any("work marker" in finding.title.lower() for finding in result.findings)
    assert any("secret" in finding.title.lower() for finding in result.findings)
    assert any("TLS" in finding.title for finding in result.findings)
    evidence = " ".join(finding.evidence for finding in result.findings)
    assert "secret-value-123" not in evidence
