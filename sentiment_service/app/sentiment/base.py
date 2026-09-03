from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas import ModelSentiment, SentimentLabel


class SentimentEngineError(RuntimeError):
    pass


def classify_score(score: float, bullish_threshold: float = 0.2, bearish_threshold: float = -0.2) -> SentimentLabel:
    if score >= bullish_threshold:
        return SentimentLabel.BULLISH
    if score <= bearish_threshold:
        return SentimentLabel.BEARISH
    return SentimentLabel.NEUTRAL


class SentimentEngine(ABC):
    name: str

    @abstractmethod
    async def analyze(self, text: str, symbol: str) -> ModelSentiment:
        pass

    def available(self) -> bool:
        return True

