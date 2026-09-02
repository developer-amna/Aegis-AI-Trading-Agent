from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from .schemas import ArticleSentiment, NormalizedArticle, SentimentLabel


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS news_articles (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    provider_article_id TEXT,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    published_at TEXT NOT NULL,
    source TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'PENDING',
    error_message TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(provider, provider_article_id), UNIQUE(url), UNIQUE(content_hash)
);
CREATE INDEX IF NOT EXISTS idx_articles_published ON news_articles(published_at);
CREATE TABLE IF NOT EXISTS article_symbols (
    article_id TEXT NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    confidence REAL NOT NULL,
    PRIMARY KEY(article_id, symbol)
);
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    model TEXT NOT NULL,
    sentiment TEXT NOT NULL,
    score REAL NOT NULL,
    confidence REAL NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(article_id, symbol, model)
);
CREATE INDEX IF NOT EXISTS idx_analysis_symbol ON sentiment_analysis(symbol, created_at);
CREATE TABLE IF NOT EXISTS market_sentiment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    score REAL NOT NULL,
    label TEXT NOT NULL,
    confidence REAL NOT NULL,
    article_count INTEGER NOT NULL,
    window_minutes INTEGER NOT NULL,
    calculated_at TEXT NOT NULL
);
"""


class SentimentRepository:
    def __init__(self, path: Path):
        self.path = path
        if str(path) != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()

    def initialize(self) -> None:
        with self._lock, self._connection:
            self._connection.executescript(SCHEMA)

    def ping(self) -> bool:
        with self._lock:
            return self._connection.execute("SELECT 1").fetchone()[0] == 1

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def article_exists(self, provider: str, provider_article_id: Optional[str], url: str, content_hash: str) -> bool:
        with self._lock:
            row = self._connection.execute(
                "SELECT 1 FROM news_articles WHERE url=? OR content_hash=? OR (provider=? AND provider_article_id=?) LIMIT 1",
                (url, content_hash, provider, provider_article_id),
            ).fetchone()
        return row is not None

    def recent_headlines(self, limit: int = 250) -> List[str]:
        with self._lock:
            rows = self._connection.execute("SELECT title FROM news_articles ORDER BY published_at DESC LIMIT ?", (limit,)).fetchall()
        return [row["title"] for row in rows]

    def save_article(self, article: NormalizedArticle, entity_confidences: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO news_articles
                (id, provider, provider_article_id, url, title, description, content, published_at, source, content_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (article.id, article.provider, article.provider_article_id, article.url, article.title, article.description,
                 article.content, article.published_at.isoformat(), article.source, article.article_hash, now),
            )
            self._connection.executemany(
                "INSERT INTO article_symbols(article_id, symbol, confidence) VALUES (?, ?, ?)",
                [(article.id, symbol, confidence) for symbol, confidence in entity_confidences.items()],
            )

    def save_sentiment(self, value: ArticleSentiment) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT OR REPLACE INTO sentiment_analysis
                (article_id, symbol, model, sentiment, score, confidence, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (value.article_id, value.symbol, value.model, value.sentiment.value, value.score,
                 value.confidence, value.reason, datetime.now(timezone.utc).isoformat()),
            )
            self._connection.execute("UPDATE news_articles SET processing_status='PROCESSED', error_message=NULL WHERE id=?", (value.article_id,))

    def mark_failed(self, article_id: str, error: str) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE news_articles SET processing_status='FAILED', error_message=? WHERE id=?",
                (error[:500], article_id),
            )

    def mark_skipped(self, article_id: str, reason: str) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE news_articles SET processing_status='SKIPPED', error_message=? WHERE id=?",
                (reason[:500], article_id),
            )

    def mark_partial(self, article_id: str, reason: str) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE news_articles SET processing_status='PARTIAL', error_message=? WHERE id=?",
                (reason[:500], article_id),
            )

    def sentiments_for_symbol(self, symbol: str, since: datetime) -> List[ArticleSentiment]:
        with self._lock:
            rows = self._connection.execute(
                """SELECT s.article_id, s.symbol, a.source, s.sentiment, s.score, s.confidence,
                          a.published_at, s.model, s.reason
                   FROM sentiment_analysis s JOIN news_articles a ON a.id=s.article_id
                   WHERE s.symbol=? AND a.published_at>=? ORDER BY a.published_at DESC""",
                (symbol.upper(), since.isoformat()),
            ).fetchall()
        return [ArticleSentiment(
            article_id=row["article_id"], symbol=row["symbol"], source=row["source"],
            sentiment=SentimentLabel(row["sentiment"]), score=row["score"], confidence=row["confidence"],
            published_at=datetime.fromisoformat(row["published_at"]), model=row["model"], reason=row["reason"],
        ) for row in rows]

    def known_symbols(self, since: datetime) -> List[str]:
        with self._lock:
            rows = self._connection.execute(
                """SELECT DISTINCT s.symbol FROM sentiment_analysis s
                   JOIN news_articles a ON a.id=s.article_id WHERE a.published_at>=?""",
                (since.isoformat(),),
            ).fetchall()
        return [row["symbol"] for row in rows]

    def save_market_sentiment(self, result) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO market_sentiment(symbol, score, label, confidence, article_count, window_minutes, calculated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (result.symbol, result.score, result.sentiment.value, result.confidence,
                 result.article_count, result.window_minutes, result.timestamp.isoformat()),
            )
