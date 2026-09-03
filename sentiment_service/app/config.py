from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def _json_map(name: str, default: Dict[str, float]) -> Dict[str, float]:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        value = json.loads(raw)
        return {str(k): float(v) for k, v in value.items()}
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


DEFAULT_COMPANIES = {
    "AAPL": ("Apple", "Apple Inc."),
    "AMZN": ("Amazon", "Amazon.com"),
    "GOOGL": ("Alphabet", "Google"),
    "META": ("Meta Platforms", "Facebook"),
    "MSFT": ("Microsoft", "Microsoft Corporation"),
    "NVDA": ("NVIDIA", "Nvidia Corporation"),
    "TSLA": ("Tesla", "Tesla Inc."),
}


def _default_database_url() -> str:
    return f"sqlite:///{Path(__file__).resolve().parents[1] / 'sentiment.db'}"


@dataclass(frozen=True)
class Settings:
    service_name: str = field(default_factory=lambda: os.getenv("SERVICE_NAME", "aegis-sentiment-service"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", _default_database_url()))
    news_api_key: Optional[str] = field(default_factory=lambda: os.getenv("NEWS_API_KEY"))
    news_api_base_url: str = field(default_factory=lambda: os.getenv("NEWS_API_BASE_URL", "https://newsapi.org/v2"))
    news_poll_interval_seconds: int = field(default_factory=lambda: int(os.getenv("NEWS_POLL_INTERVAL_SECONDS", "60")))
    sentiment_lookback_minutes: int = field(default_factory=lambda: int(os.getenv("SENTIMENT_LOOKBACK_MINUTES", "60")))
    bullish_threshold: float = field(default_factory=lambda: float(os.getenv("SENTIMENT_BULLISH_THRESHOLD", "0.20")))
    bearish_threshold: float = field(default_factory=lambda: float(os.getenv("SENTIMENT_BEARISH_THRESHOLD", "-0.20")))
    stale_after_minutes: int = field(default_factory=lambda: int(os.getenv("SENTIMENT_STALE_AFTER_MINUTES", "15")))
    sentiment_cache_ttl_seconds: int = field(default_factory=lambda: int(os.getenv("SENTIMENT_CACHE_TTL_SECONDS", "15")))
    decay_half_life_minutes: float = field(default_factory=lambda: float(os.getenv("SENTIMENT_DECAY_HALF_LIFE_MINUTES", "60")))
    min_article_chars: int = field(default_factory=lambda: int(os.getenv("MIN_ARTICLE_CHARS", "80")))
    max_article_chars: int = field(default_factory=lambda: int(os.getenv("MAX_ARTICLE_CHARS", "12000")))
    min_model_confidence: float = field(default_factory=lambda: float(os.getenv("MIN_MODEL_CONFIDENCE", "0.55")))
    finbert_model: str = field(default_factory=lambda: os.getenv("FINBERT_MODEL", "ProsusAI/finbert"))
    finbert_enabled: bool = field(default_factory=lambda: _bool("FINBERT_ENABLED", True))
    llm_enabled: bool = field(default_factory=lambda: _bool("LLM_ENABLED", False))
    llm_api_key: Optional[str] = field(default_factory=lambda: os.getenv("LLM_API_KEY"))
    llm_base_url: Optional[str] = field(default_factory=lambda: os.getenv("LLM_BASE_URL"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4.1-mini"))
    worker_enabled: bool = field(default_factory=lambda: _bool("WORKER_ENABLED", False))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("SENTIMENT_SERVICE_API_KEY"))
    source_weights: Dict[str, float] = field(default_factory=lambda: _json_map("SOURCE_WEIGHTS_JSON", {}))
    scraper_feeds: Tuple[str, ...] = field(default_factory=lambda: tuple(x.strip() for x in os.getenv("SCRAPER_FEED_URLS", "").split(",") if x.strip()))
    supported_companies: Dict[str, Tuple[str, ...]] = field(default_factory=lambda: DEFAULT_COMPANIES.copy())

    @property
    def database_path(self) -> Path:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            raise ValueError("Only sqlite DATABASE_URL values are currently supported")
        return Path(self.database_url[len(prefix):]).expanduser()
