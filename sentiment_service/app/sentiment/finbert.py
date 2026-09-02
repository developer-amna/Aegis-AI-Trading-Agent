from __future__ import annotations

import asyncio
import importlib.util
from typing import Any, Dict, Optional

from .base import SentimentEngine, SentimentEngineError, classify_score
from ..schemas import ModelSentiment


class FinBERTEngine(SentimentEngine):
    name = "finbert"

    def __init__(self, model_name: str = "ProsusAI/finbert", enabled: bool = True):
        self.model_name = model_name
        self.enabled = enabled
        self._pipeline: Any = None
        self._load_error: Optional[Exception] = None

    def _load(self) -> Any:
        if not self.enabled:
            raise SentimentEngineError("FinBERT is disabled")
        if self._load_error:
            raise SentimentEngineError(f"FinBERT unavailable: {self._load_error}")
        if self._pipeline is None:
            try:
                from transformers import pipeline

                self._pipeline = pipeline("text-classification", model=self.model_name, tokenizer=self.model_name, top_k=None)
            except Exception as exc:
                self._load_error = exc
                raise SentimentEngineError(f"FinBERT unavailable: {exc}") from exc
        return self._pipeline

    def _analyze_sync(self, text: str) -> ModelSentiment:
        classifier = self._load()
        try:
            raw = classifier(text, truncation=True, max_length=512)
            rows = raw[0] if raw and isinstance(raw[0], list) else raw
            probabilities: Dict[str, float] = {str(row["label"]).lower(): float(row["score"]) for row in rows}
            positive = probabilities.get("positive", probabilities.get("label_2", 0.0))
            negative = probabilities.get("negative", probabilities.get("label_0", 0.0))
            neutral = probabilities.get("neutral", probabilities.get("label_1", 0.0))
            score = max(-1.0, min(1.0, positive - negative))
            confidence = max(positive, negative, neutral)
            return ModelSentiment(
                sentiment=classify_score(score), score=score, confidence=confidence,
                reason="FinBERT probability-weighted classification", model=self.model_name,
                probabilities={"positive": positive, "negative": negative, "neutral": neutral},
            )
        except SentimentEngineError:
            raise
        except Exception as exc:
            raise SentimentEngineError(f"FinBERT inference failed: {exc}") from exc

    async def analyze(self, text: str, symbol: str) -> ModelSentiment:
        return await asyncio.to_thread(self._analyze_sync, text)

    def available(self) -> bool:
        return self.enabled and self._load_error is None and importlib.util.find_spec("transformers") is not None
