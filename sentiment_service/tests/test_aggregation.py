from datetime import datetime, timedelta, timezone

import pytest

from sentiment_service.app.schemas import ArticleSentiment, DataStatus, SentimentLabel
from sentiment_service.app.sentiment import SentimentAggregator


NOW = datetime(2026, 9, 2, 11, 0, tzinfo=timezone.utc)


def row(score, confidence=1.0, minutes_old=0, source="Wire", article_id="a"):
    label = "BULLISH" if score >= 0.2 else "BEARISH" if score <= -0.2 else "NEUTRAL"
    return ArticleSentiment(
        article_id=f"{article_id}-{score}-{minutes_old}", symbol="AAPL", source=source,
        sentiment=label, score=score, confidence=confidence,
        published_at=NOW - timedelta(minutes=minutes_old), model="fixture",
    )


@pytest.mark.parametrize("scores,label", [([0.8, 0.6], SentimentLabel.BULLISH), ([-0.8, -0.6], SentimentLabel.BEARISH)])
def test_consistent_article_aggregation(scores, label):
    result = SentimentAggregator().aggregate("AAPL", [row(x, article_id=str(i)) for i, x in enumerate(scores)], 60, NOW)
    assert result.sentiment == label
    assert result.data_status == DataStatus.FRESH


def test_mixed_confidence_and_recency_weighting():
    aggregator = SentimentAggregator(half_life_minutes=10)
    result = aggregator.aggregate("AAPL", [row(0.9, 0.95, 1, article_id="new"), row(-0.9, 0.2, 50, article_id="old")], 60, NOW)
    assert result.score > 0.8
    assert result.sentiment == SentimentLabel.BULLISH


def test_source_weighting():
    aggregator = SentimentAggregator(source_weights={"Trusted": 1.0, "Other": 0.2})
    result = aggregator.aggregate("AAPL", [row(0.8, source="Trusted"), row(-0.8, source="Other", article_id="b")], 60, NOW)
    assert result.score > 0.5


def test_no_news_and_stale_news_are_explicit():
    aggregator = SentimentAggregator(stale_after_minutes=15)
    empty = aggregator.aggregate("AAPL", [], 60, NOW)
    assert empty.data_status == DataStatus.INSUFFICIENT_DATA
    assert empty.article_count == 0 and empty.confidence == 0
    stale = aggregator.aggregate("AAPL", [row(0.5, minutes_old=20)], 60, NOW)
    assert stale.data_status == DataStatus.STALE


def test_market_aggregation_caps_each_symbol_contribution():
    aggregator = SentimentAggregator()
    aapl = aggregator.aggregate("AAPL", [row(0.8, article_id=str(i)) for i in range(20)], 60, NOW)
    tsla_rows = [row(-0.8, article_id="tsla")]
    tsla_rows[0] = tsla_rows[0].model_copy(update={"symbol": "TSLA"})
    tsla = aggregator.aggregate("TSLA", tsla_rows, 60, NOW)
    market = aggregator.aggregate_market([aapl, tsla], 60, NOW)
    assert abs(market.score) < 0.2  # 20 AAPL stories do not count as 20 symbol votes.

