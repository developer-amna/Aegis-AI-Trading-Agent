from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SentimentLabel(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class DataStatus(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"


class NormalizedArticle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    provider: str
    provider_article_id: Optional[str] = None
    source: str
    title: str
    description: str = ""
    content: str = ""
    url: str
    published_at: datetime
    symbols: List[str] = Field(default_factory=list)
    company_names: List[str] = Field(default_factory=list)
    article_hash: Optional[str] = None

    @field_validator("published_at")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class ModelSentiment(BaseModel):
    sentiment: SentimentLabel
    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: Optional[str] = None
    model: str
    probabilities: Dict[str, float] = Field(default_factory=dict)


class ArticleSentiment(BaseModel):
    article_id: str
    symbol: str
    source: str
    sentiment: SentimentLabel
    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    published_at: datetime
    model: str
    reason: Optional[str] = None


class SentimentResponse(BaseModel):
    symbol: str
    sentiment: SentimentLabel
    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    article_count: int = Field(ge=0)
    timestamp: datetime
    data_timestamp: Optional[datetime] = None
    window_minutes: int
    data_status: DataStatus


class BatchRequest(BaseModel):
    symbols: List[str] = Field(min_length=1, max_length=100)
    window_minutes: Optional[int] = Field(default=None, ge=1, le=1440)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, values: List[str]) -> List[str]:
        result = []
        for value in values:
            symbol = value.strip().upper()
            if symbol and symbol not in result:
                result.append(symbol)
        if not result:
            raise ValueError("at least one symbol is required")
        return result


class BatchResponse(BaseModel):
    results: List[SentimentResponse]
    timestamp: datetime


class MarketResponse(BaseModel):
    market_sentiment: SentimentResponse


class HealthResponse(BaseModel):
    status: str
    service: str
    checks: Dict[str, str] = Field(default_factory=dict)

