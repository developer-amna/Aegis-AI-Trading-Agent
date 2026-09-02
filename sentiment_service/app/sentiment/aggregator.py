from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from .base import classify_score
from ..schemas import ArticleSentiment, DataStatus, SentimentLabel, SentimentResponse


class SentimentAggregator:
    def __init__(
        self,
        bullish_threshold: float = 0.2,
        bearish_threshold: float = -0.2,
        half_life_minutes: float = 60.0,
        stale_after_minutes: int = 15,
        source_weights: Optional[Dict[str, float]] = None,
    ):
        self.bullish_threshold = bullish_threshold
        self.bearish_threshold = bearish_threshold
        self.half_life_minutes = max(0.01, half_life_minutes)
        self.stale_after_minutes = stale_after_minutes
        self.source_weights = {key.casefold(): value for key, value in (source_weights or {}).items()}

    def _weight(self, item: ArticleSentiment, now: datetime) -> float:
        age_minutes = max(0.0, (now - item.published_at.astimezone(timezone.utc)).total_seconds() / 60.0)
        recency = math.exp(-math.log(2) * age_minutes / self.half_life_minutes)
        source = max(0.0, self.source_weights.get(item.source.casefold(), 1.0))
        return item.confidence * source * recency

    def aggregate(self, symbol: str, articles: Iterable[ArticleSentiment], window_minutes: int, now: Optional[datetime] = None) -> SentimentResponse:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        rows = list(articles)
        if not rows:
            return SentimentResponse(
                symbol=symbol.upper(), sentiment=SentimentLabel.NEUTRAL, score=0.0, confidence=0.0,
                article_count=0, timestamp=now, data_timestamp=None, window_minutes=window_minutes,
                data_status=DataStatus.INSUFFICIENT_DATA,
            )
        weighted = [(row, self._weight(row, now)) for row in rows]
        total_weight = sum(weight for _, weight in weighted)
        if total_weight <= 0:
            score, confidence = 0.0, 0.0
        else:
            score = sum(row.score * weight for row, weight in weighted) / total_weight
            confidence = sum(row.confidence * weight for row, weight in weighted) / total_weight
            confidence *= min(1.0, math.sqrt(len(rows) / 3.0))
        score = max(-1.0, min(1.0, score))
        confidence = max(0.0, min(1.0, confidence))
        data_timestamp = max(row.published_at for row in rows)
        age = (now - data_timestamp.astimezone(timezone.utc)).total_seconds() / 60.0
        status = DataStatus.STALE if age > self.stale_after_minutes else DataStatus.FRESH
        return SentimentResponse(
            symbol=symbol.upper(), sentiment=classify_score(score, self.bullish_threshold, self.bearish_threshold),
            score=score, confidence=confidence, article_count=len(rows), timestamp=now,
            data_timestamp=data_timestamp, window_minutes=window_minutes, data_status=status,
        )

    def aggregate_market(self, symbol_results: Iterable[SentimentResponse], window_minutes: int, now: Optional[datetime] = None) -> SentimentResponse:
        now = now or datetime.now(timezone.utc)
        usable = [row for row in symbol_results if row.article_count > 0 and row.data_status != DataStatus.ERROR]
        if not usable:
            return self.aggregate("MARKET", [], window_minutes, now)
        # Each symbol contributes once, preventing a high-volume ticker from dominating.
        # Equal symbol weighting is deliberate: per-symbol confidence already
        # reflects evidence quality, while weighting the market score by it would
        # reintroduce an article-volume bias through confidence saturation.
        score = sum(row.score for row in usable) / len(usable)
        confidence = sum(row.confidence for row in usable) / len(usable)
        freshest = max((row.data_timestamp for row in usable if row.data_timestamp), default=None)
        status = DataStatus.FRESH if any(row.data_status == DataStatus.FRESH for row in usable) else DataStatus.STALE
        return SentimentResponse(
            symbol="MARKET", sentiment=classify_score(score, self.bullish_threshold, self.bearish_threshold),
            score=max(-1.0, min(1.0, score)), confidence=max(0.0, min(1.0, confidence)),
            article_count=sum(row.article_count for row in usable), timestamp=now, data_timestamp=freshest,
            window_minutes=window_minutes, data_status=status,
        )
