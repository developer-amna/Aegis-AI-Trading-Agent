from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional

from ..processing.cleaner import ArticleCleaner, InvalidArticleError
from ..processing.deduplicator import ArticleDeduplicator
from ..processing.entity_extractor import EntityExtractor
from ..processing.relevance import FinancialRelevanceFilter
from ..providers.base import NewsProvider, ProviderError
from ..schemas import ArticleSentiment, NormalizedArticle
from ..sentiment.base import SentimentEngine, SentimentEngineError

logger = logging.getLogger(__name__)


class NewsSentimentPipeline:
    def __init__(self, providers: List[NewsProvider], repository, cleaner: ArticleCleaner, deduplicator: ArticleDeduplicator,
                 entity_extractor: EntityExtractor, engine: SentimentEngine, lookback_minutes: int = 1440,
                 relevance_filter: Optional[FinancialRelevanceFilter] = None):
        self.providers = providers
        self.repository = repository
        self.cleaner = cleaner
        self.deduplicator = deduplicator
        self.entity_extractor = entity_extractor
        self.engine = engine
        self.lookback_minutes = lookback_minutes
        self.relevance_filter = relevance_filter or FinancialRelevanceFilter()

    async def run_once(self, symbols: Optional[List[str]] = None, now: Optional[datetime] = None) -> dict:
        now = now or datetime.now(timezone.utc)
        since = now - timedelta(minutes=self.lookback_minutes)
        request_id = str(uuid.uuid4())
        stats = {"received": 0, "processed": 0, "duplicates": 0, "skipped": 0, "failed": 0, "provider_errors": 0}
        for provider in self.providers:
            logger.info("NEWS_FETCH_STARTED", extra={"request_id": request_id, "provider": provider.name})
            try:
                articles = await provider.fetch(since, symbols)
                logger.info("NEWS_FETCH_COMPLETED", extra={"request_id": request_id, "provider": provider.name, "article_count": len(articles)})
            except ProviderError:
                stats["provider_errors"] += 1
                logger.exception("NEWS_FETCH_FAILED", extra={"request_id": request_id, "provider": provider.name})
                continue
            for article in articles:
                stats["received"] += 1
                outcome = await self.process_article(article, request_id, now)
                stats[outcome] += 1
        return stats

    async def process_article(self, article: NormalizedArticle, request_id: Optional[str] = None,
                              now: Optional[datetime] = None) -> str:
        context = {"request_id": request_id or str(uuid.uuid4()), "article_id": article.id, "provider": article.provider}
        logger.info("ARTICLE_RECEIVED", extra=context)
        try:
            if article.published_at < (now or datetime.now(timezone.utc)) - timedelta(minutes=self.lookback_minutes):
                return "skipped"
            cleaned = self.cleaner.clean(article)
            normalized_url = self.deduplicator.normalize_url(cleaned.url)
            article_hash = self.deduplicator.identify(cleaned)
            cleaned = cleaned.model_copy(update={"url": normalized_url, "article_hash": article_hash})
            if self.deduplicator.is_duplicate(cleaned):
                logger.info("ARTICLE_DUPLICATE", extra=context)
                return "duplicates"
            entities = self.entity_extractor.extract(cleaned)
            if not entities:
                self.repository.save_article(cleaned, {})
                self.repository.mark_skipped(cleaned.id, "no supported symbol")
                logger.info("ARTICLE_NO_SUPPORTED_SYMBOL", extra=context)
                return "skipped"
            cleaned = cleaned.model_copy(update={"symbols": [x[0] for x in entities], "company_names": [x[1] for x in entities]})
            confidences = {symbol: confidence for symbol, _, confidence in entities}
            self.repository.save_article(cleaned, confidences)
            if not self.relevance_filter.is_relevant(cleaned):
                self.repository.mark_skipped(cleaned.id, "not financially relevant")
                logger.info("ARTICLE_NOT_FINANCIALLY_RELEVANT", extra=context)
                return "skipped"
            logger.info("ARTICLE_PARSED", extra={**context, "symbols": cleaned.symbols})
            text = f"{cleaned.title}. {cleaned.content}"
            successes = 0
            failures = 0
            for symbol in cleaned.symbols:
                try:
                    logger.info("SENTIMENT_ANALYSIS_STARTED", extra={**context, "symbol": symbol})
                    model_result = await self.engine.analyze(text, symbol)
                    result = ArticleSentiment(
                        article_id=cleaned.id, symbol=symbol, source=cleaned.source,
                        sentiment=model_result.sentiment, score=model_result.score,
                        confidence=model_result.confidence * confidences[symbol], published_at=cleaned.published_at,
                        model=model_result.model, reason=model_result.reason,
                    )
                    self.repository.save_sentiment(result)
                    successes += 1
                    logger.info("SENTIMENT_ANALYSIS_COMPLETED", extra={**context, "symbol": symbol, "score": result.score})
                except Exception as exc:
                    failures += 1
                    logger.exception("SENTIMENT_ANALYSIS_FAILED", extra={**context, "symbol": symbol})
                    self.repository.mark_failed(cleaned.id, str(exc))
            if successes and failures:
                self.repository.mark_partial(cleaned.id, "one or more symbol analyses failed")
            return "processed" if successes else "failed"
        except InvalidArticleError:
            logger.info("ARTICLE_INVALID", extra=context)
            return "skipped"
        except Exception:
            # A single malformed article or DB write must not terminate the batch.
            logger.exception("ARTICLE_PROCESSING_FAILED", extra=context)
            return "failed"
