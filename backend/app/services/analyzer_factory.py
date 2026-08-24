"""Select the semantic analyzer available in the current environment."""

import os

from app.services.ai_analyzer import AIAnalyzer, fallback_analysis
from app.services.openai_analyzer import OpenAIAnalyzer


class FallbackAnalyzer:
    def analyze(self, context: str):
        return fallback_analysis([])


def get_analyzer() -> AIAnalyzer:
    """Prefer OpenAI when configured, otherwise use a safe local fallback."""
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIAnalyzer()
    return FallbackAnalyzer()
