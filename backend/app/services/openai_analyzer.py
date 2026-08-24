"""OpenAI-backed semantic repository analyzer.

The adapter is optional: without OPENAI_API_KEY the application keeps using the
safe deterministic baseline analyzer.
"""

import json
import os

from app.models.findings import AnalysisResult
from app.services.ai_analyzer import SYSTEM_PROMPT


class OpenAIAnalyzer:
    """Analyze bounded repository context with the OpenAI Responses API."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
        self.api_key = os.getenv("OPENAI_API_KEY")

    def analyze(self, context: str) -> AnalysisResult:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

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
        return AnalysisResult.model_validate(json.loads(response.output_text))
