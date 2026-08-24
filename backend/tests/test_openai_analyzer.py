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
