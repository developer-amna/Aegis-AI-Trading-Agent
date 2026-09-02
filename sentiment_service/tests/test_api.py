from dataclasses import replace
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from sentiment_service.app.config import Settings
from sentiment_service.app.container import build_container
from sentiment_service.app.main import create_app
from sentiment_service.app.schemas import ArticleSentiment, NormalizedArticle


@pytest.fixture
def client(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'api.db'}", finbert_enabled=False, worker_enabled=False)
    container = build_container(settings)
    app = create_app(settings, container)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client, container


def seed(container, symbol="AAPL"):
    published = datetime.now(timezone.utc)
    article = NormalizedArticle(
        id=f"seed-{symbol}", provider="test", provider_article_id=f"p-{symbol}", source="Reuters",
        title=f"{symbol} financial results", content="A sufficiently long article body for API aggregation and persistence testing.",
        url=f"https://example.test/{symbol}", published_at=published, article_hash=f"hash-{symbol}",
    )
    container.repository.save_article(article, {symbol: 1.0})
    container.repository.save_sentiment(ArticleSentiment(
        article_id=article.id, symbol=symbol, source="Reuters", sentiment="BULLISH", score=0.7,
        confidence=0.9, published_at=published, model="fixture",
    ))


def test_health_and_no_news_contract(client):
    http, _ = client
    assert http.get("/health").status_code == 200
    response = http.get("/api/v1/sentiment/AAPL")
    assert response.status_code == 200
    body = response.json()
    assert body["data_status"] == "INSUFFICIENT_DATA"
    assert body["article_count"] == 0 and body["confidence"] == 0


def test_valid_invalid_and_batch_requests(client):
    http, container = client
    seed(container, "AAPL")
    response = http.get("/api/v1/sentiment/aapl")
    assert response.status_code == 200
    assert response.json()["sentiment"] == "BULLISH"
    assert http.get("/api/v1/sentiment/INVALID").status_code == 404
    batch = http.post("/api/v1/sentiment/batch", json={"symbols": ["AAPL", "NVDA"]})
    assert batch.status_code == 200 and len(batch.json()["results"]) == 2
    assert http.post("/api/v1/sentiment/batch", json={"symbols": []}).status_code == 422


def test_market_endpoint_and_authentication(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'auth.db'}", finbert_enabled=False, api_key="secret")
    container = build_container(settings)
    with TestClient(create_app(settings, container)) as http:
        assert http.get("/api/v1/sentiment/AAPL").status_code == 401
        assert http.get("/api/v1/sentiment/AAPL", headers={"X-API-Key": "secret"}).status_code == 200
        assert http.get("/api/v1/sentiment/market", headers={"X-API-Key": "secret"}).status_code == 200


def test_database_failure_returns_service_unavailable(client):
    http, container = client
    container.repository.close()
    assert http.get("/api/v1/sentiment/AAPL").status_code == 503
