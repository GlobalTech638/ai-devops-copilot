import json

import pytest

from app.services.openai_analyzer import _parse_result


def test_parse_result_validates_structured_output():
    result = _parse_result(json.dumps({"summary": "ok", "findings": []}))
    assert result.summary == "ok"
    assert result.findings == []


def test_parse_result_rejects_invalid_json():
    with pytest.raises(ValueError, match="invalid JSON"):
        _parse_result("not-json")


def test_openai_analyzer_uses_supported_default_model(monkeypatch):
    from app.services.openai_analyzer import OpenAIAnalyzer

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    analyzer = OpenAIAnalyzer()
    assert analyzer.model == "gpt-4.1-mini"


def test_openai_analyzer_rejects_missing_api_key(monkeypatch):
    from app.services.openai_analyzer import OpenAIAnalyzer

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not configured"):
        OpenAIAnalyzer()
