from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional


class SentimentQueryService:
    def __init__(self, repository, aggregator, default_window_minutes: int, supported_symbols, cache_ttl_seconds: int = 15):
        self.repository = repository
        self.aggregator = aggregator
        self.default_window_minutes = default_window_minutes
        self.supported_symbols = {symbol.upper() for symbol in supported_symbols}
        self.cache_ttl_seconds = max(0, cache_ttl_seconds)
        self._cache = {}

    def validate_symbol(self, symbol: str) -> str:
        normalized = symbol.strip().upper()
        if normalized not in self.supported_symbols:
            raise ValueError(f"unsupported symbol: {normalized}")
        return normalized

    def get(self, symbol: str, window_minutes: Optional[int] = None, now: Optional[datetime] = None):
        symbol = self.validate_symbol(symbol)
        window = window_minutes or self.default_window_minutes
        now = now or datetime.now(timezone.utc)
        cache_key = (symbol, window)
        cached = self._cache.get(cache_key)
        if cached and (now - cached.timestamp).total_seconds() <= self.cache_ttl_seconds:
            return cached
        rows = self.repository.sentiments_for_symbol(symbol, now - timedelta(minutes=window))
        result = self.aggregator.aggregate(symbol, rows, window, now)
        self.repository.save_market_sentiment(result)
        self._cache[cache_key] = result
        return result

    def market(self, window_minutes: Optional[int] = None, now: Optional[datetime] = None):
        window = window_minutes or self.default_window_minutes
        now = now or datetime.now(timezone.utc)
        symbols = self.repository.known_symbols(now - timedelta(minutes=window))
        results = [self.get(symbol, window, now) for symbol in symbols if symbol in self.supported_symbols]
        result = self.aggregator.aggregate_market(results, window, now)
        self.repository.save_market_sentiment(result)
        return result
