PRAGMA foreign_keys = ON;

CREATE TABLE news_articles (
  id TEXT PRIMARY KEY, provider TEXT NOT NULL, provider_article_id TEXT,
  url TEXT NOT NULL UNIQUE, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
  content TEXT NOT NULL, published_at TEXT NOT NULL, source TEXT NOT NULL,
  content_hash TEXT NOT NULL UNIQUE, processing_status TEXT NOT NULL DEFAULT 'PENDING',
  error_message TEXT, created_at TEXT NOT NULL,
  UNIQUE(provider, provider_article_id)
);
CREATE INDEX idx_articles_published ON news_articles(published_at);

CREATE TABLE article_symbols (
  article_id TEXT NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL, confidence REAL NOT NULL, PRIMARY KEY(article_id, symbol)
);

CREATE TABLE sentiment_analysis (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id TEXT NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL, model TEXT NOT NULL, sentiment TEXT NOT NULL,
  score REAL NOT NULL, confidence REAL NOT NULL, reason TEXT, created_at TEXT NOT NULL,
  UNIQUE(article_id, symbol, model)
);
CREATE INDEX idx_analysis_symbol ON sentiment_analysis(symbol, created_at);

CREATE TABLE market_sentiment (
  id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL, score REAL NOT NULL,
  label TEXT NOT NULL, confidence REAL NOT NULL, article_count INTEGER NOT NULL,
  window_minutes INTEGER NOT NULL, calculated_at TEXT NOT NULL
);

