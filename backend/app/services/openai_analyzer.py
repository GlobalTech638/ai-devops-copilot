"""OpenAI-backed semantic repository analyzer."""

import json
import os
from typing import Any

from app.models.findings import AnalysisResult
from app.services.ai_analyzer import SYSTEM_PROMPT


class OpenAIAnalyzer:
    """Analyze bounded repository context with the OpenAI Responses API."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

    def analyze(self, context: str) -> AnalysisResult:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            text={"format": {
                "type": "json_schema",
                "name": "analysis_result",
                "strict": True,
                "schema": AnalysisResult.model_json_schema(),
            }},
        )
        return _parse_result(response.output_text)


def _parse_result(output: str) -> AnalysisResult:
    """Validate model output at the application boundary."""
    try:
        payload: Any = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError("AI provider returned invalid JSON") from exc
    return AnalysisResult.model_validate(payload)
