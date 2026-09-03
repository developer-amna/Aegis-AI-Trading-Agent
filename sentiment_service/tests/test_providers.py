import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from sentiment_service.app.providers import NewsAPIProvider, ProviderError, ProviderRateLimitError


def fixture_payload():
    return json.loads((Path(__file__).parent / "fixtures" / "newsapi_response.json").read_text())


@pytest.mark.asyncio
async def test_news_api_success_and_normalization():
    async def handler(request):
        assert request.headers["X-Api-Key"] == "test-key"
        return httpx.Response(200, json=fixture_payload())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        rows = await NewsAPIProvider("test-key", "https://news.test", client).fetch(
            datetime(2026, 9, 2, tzinfo=timezone.utc), ["AAPL"]
        )
    assert len(rows) == 2
    assert rows[0].source == "Reuters"
    assert rows[0].published_at.tzinfo is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{}, {"status": "error"}, {"status": "ok", "articles": "bad"}])
async def test_news_api_invalid_response(payload):
    async def handler(request):
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ProviderError):
            await NewsAPIProvider("key", client=client).fetch(datetime.now(timezone.utc))


@pytest.mark.asyncio
async def test_news_api_empty_response():
    async def handler(request):
        return httpx.Response(200, json={"status": "ok", "articles": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert await NewsAPIProvider("key", client=client).fetch(datetime.now(timezone.utc)) == []


@pytest.mark.asyncio
async def test_news_api_timeout_and_rate_limit():
    async def timeout(request):
        raise httpx.ReadTimeout("timed out", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(timeout)) as client:
        with pytest.raises(ProviderError):
            await NewsAPIProvider("key", client=client).fetch(datetime.now(timezone.utc))

    async def limited(request):
        return httpx.Response(429)

    async with httpx.AsyncClient(transport=httpx.MockTransport(limited)) as client:
        with pytest.raises(ProviderRateLimitError):
            await NewsAPIProvider("key", client=client).fetch(datetime.now(timezone.utc))

