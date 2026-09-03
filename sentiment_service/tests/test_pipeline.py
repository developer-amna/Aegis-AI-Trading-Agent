from datetime import datetime, timedelta, timezone

import pytest

from sentiment_service.app.processing import ArticleCleaner, ArticleDeduplicator, EntityExtractor
from sentiment_service.app.providers.base import NewsProvider, ProviderError
from sentiment_service.app.schemas import ModelSentiment, NormalizedArticle
from sentiment_service.app.sentiment import SentimentEngine
from sentiment_service.app.services import NewsSentimentPipeline


class FixtureProvider(NewsProvider):
    name = "fixture"
    def __init__(self, articles=None, error=None):
        self.articles, self.error = articles or [], error
    async def fetch(self, since, symbols=None):
        if self.error:
            raise self.error
        return self.articles


class KeywordEngine(SentimentEngine):
    name = "fixture-model"
    async def analyze(self, text, symbol):
        if "beat" in text.lower() and "raised" in text.lower():
            return ModelSentiment(sentiment="BULLISH", score=0.75, confidence=0.9, model=self.name, reason="beat and raised")
        return ModelSentiment(sentiment="BEARISH", score=-0.7, confidence=0.85, model=self.name, reason="weaker outlook")


def fixture_article(article_id="article-1", title="Apple beats earnings and raised guidance", content=None):
    return NormalizedArticle(
        id=article_id, provider="fixture", provider_article_id=article_id, source="Reuters",
        title=title, description="Apple Inc. released quarterly financial results.",
        content=content or "Apple beat consensus revenue expectations and raised full-year guidance as demand improved significantly.",
        url=f"https://example.test/{article_id}", published_at=datetime.now(timezone.utc),
    )


def build_pipeline(repository, providers):
    return NewsSentimentPipeline(
        providers, repository, ArticleCleaner(min_chars=40), ArticleDeduplicator(repository),
        EntityExtractor({"AAPL": ("Apple", "Apple Inc."), "TSLA": ("Tesla", "Tesla Inc.")}),
        KeywordEngine(), lookback_minutes=60,
    )


@pytest.mark.asyncio
async def test_realistic_end_to_end_article_flow(repository):
    pipeline = build_pipeline(repository, [FixtureProvider([fixture_article()])])
    stats = await pipeline.run_once()
    rows = repository.sentiments_for_symbol("AAPL", datetime.now(timezone.utc) - timedelta(hours=1))
    assert stats == {"received": 1, "processed": 1, "duplicates": 0, "skipped": 0, "failed": 0, "provider_errors": 0}
    assert len(rows) == 1 and rows[0].score == 0.75
    assert (await pipeline.run_once())["duplicates"] == 1


@pytest.mark.asyncio
async def test_bad_article_does_not_stop_pipeline(repository):
    bad = fixture_article("bad", title="Apple", content="x").model_copy(update={"description": ""})
    good = fixture_article("good")
    stats = await build_pipeline(repository, [FixtureProvider([bad, good])]).run_once()
    assert stats["skipped"] == 1
    assert stats["processed"] == 1


@pytest.mark.asyncio
async def test_provider_error_is_isolated(repository):
    pipeline = build_pipeline(repository, [FixtureProvider(error=ProviderError("timeout")), FixtureProvider([fixture_article()])])
    stats = await pipeline.run_once()
    assert stats["provider_errors"] == 1
    assert stats["processed"] == 1


@pytest.mark.asyncio
async def test_nonfinancial_and_unsupported_articles_are_cached_as_skipped(repository):
    lifestyle = fixture_article(
        "lifestyle", title="Apple opens a colorful downtown store",
        content="Apple welcomed visitors to a new retail space featuring local art, music, and community workshops.",
    ).model_copy(update={"description": "Apple Inc. hosted a public opening celebration for local residents."})
    unsupported = fixture_article(
        "unsupported", title="Acme beats annual revenue forecast",
        content="Acme Corporation beat its annual revenue forecast after reporting stronger customer demand.",
    ).model_copy(update={"description": "Acme published its financial results."})
    pipeline = build_pipeline(repository, [FixtureProvider([lifestyle, unsupported])])
    first = await pipeline.run_once()
    second = await pipeline.run_once()
    assert first["skipped"] == 2
    assert second["duplicates"] == 2
