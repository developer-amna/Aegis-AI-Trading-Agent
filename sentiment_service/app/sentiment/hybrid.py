from __future__ import annotations

from typing import Optional

from .base import SentimentEngine, SentimentEngineError
from ..schemas import ModelSentiment


class HybridSentimentEngine(SentimentEngine):
    name = "hybrid"

    def __init__(self, primary: SentimentEngine, fallback: Optional[SentimentEngine], minimum_confidence: float = 0.55):
        self.primary = primary
        self.fallback = fallback
        self.minimum_confidence = minimum_confidence

    async def analyze(self, text: str, symbol: str) -> ModelSentiment:
        primary_error = None
        try:
            result = await self.primary.analyze(text, symbol)
            if result.confidence >= self.minimum_confidence or not self.fallback or not self.fallback.available():
                return result
        except SentimentEngineError as exc:
            primary_error = exc
        if self.fallback and self.fallback.available():
            return await self.fallback.analyze(text, symbol)
        raise primary_error or SentimentEngineError("No sentiment engine is available")

    def available(self) -> bool:
        return self.primary.available() or bool(self.fallback and self.fallback.available())

