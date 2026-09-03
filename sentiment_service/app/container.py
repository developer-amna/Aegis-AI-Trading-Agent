from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .processing import ArticleCleaner, ArticleDeduplicator, EntityExtractor
from .providers import NewsAPIProvider, RSSScraperProvider
from .repository import SentimentRepository
from .sentiment import FinBERTEngine, HybridSentimentEngine, LLMEngine, SentimentAggregator
from .services import NewsSentimentPipeline, SentimentQueryService
from .workers import IngestionWorker


@dataclass
class Container:
    settings: Settings
    repository: SentimentRepository
    pipeline: NewsSentimentPipeline
    query_service: SentimentQueryService
    engine: HybridSentimentEngine
    worker: IngestionWorker


def build_container(settings: Settings) -> Container:
    repository = SentimentRepository(settings.database_path)
    repository.initialize()
    providers = []
    if settings.news_api_key:
        providers.append(NewsAPIProvider(settings.news_api_key, settings.news_api_base_url))
    if settings.scraper_feeds:
        providers.append(RSSScraperProvider(list(settings.scraper_feeds)))
    primary = FinBERTEngine(settings.finbert_model, settings.finbert_enabled)
    fallback = LLMEngine(settings.llm_api_key, settings.llm_model, settings.llm_base_url) if settings.llm_enabled else None
    engine = HybridSentimentEngine(primary, fallback, settings.min_model_confidence)
    cleaner = ArticleCleaner(settings.min_article_chars, settings.max_article_chars)
    deduplicator = ArticleDeduplicator(repository)
    extractor = EntityExtractor(settings.supported_companies)
    aggregator = SentimentAggregator(
        settings.bullish_threshold, settings.bearish_threshold, settings.decay_half_life_minutes,
        settings.stale_after_minutes, settings.source_weights,
    )
    pipeline = NewsSentimentPipeline(providers, repository, cleaner, deduplicator, extractor, engine, settings.sentiment_lookback_minutes)
    query = SentimentQueryService(
        repository, aggregator, settings.sentiment_lookback_minutes, settings.supported_companies,
        settings.sentiment_cache_ttl_seconds,
    )
    worker = IngestionWorker(pipeline, settings.news_poll_interval_seconds)
    return Container(settings, repository, pipeline, query, engine, worker)
