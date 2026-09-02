from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from .base import NewsProvider, ProviderError, ProviderRateLimitError
from ..schemas import NormalizedArticle


class NewsAPIProvider(NewsProvider):
    name = "newsapi"

    def __init__(self, api_key: str, base_url: str = "https://newsapi.org/v2", client: Optional[httpx.AsyncClient] = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = client

    async def fetch(self, since: datetime, symbols: Optional[List[str]] = None) -> List[NormalizedArticle]:
        query = " OR ".join(symbols or ["stocks", "earnings", "markets"])
        params = {
            "q": query,
            "from": since.astimezone(timezone.utc).isoformat(),
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 100,
        }
        own_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=15.0)
        try:
            response = await client.get(f"{self.base_url}/everything", params=params, headers={"X-Api-Key": self.api_key})
            if response.status_code == 429:
                raise ProviderRateLimitError("NewsAPI rate limit reached")
            response.raise_for_status()
            payload = response.json()
        except ProviderError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"NewsAPI request failed: {exc}") from exc
        finally:
            if own_client:
                await client.aclose()
        if not isinstance(payload, dict) or payload.get("status") != "ok" or not isinstance(payload.get("articles"), list):
            raise ProviderError("NewsAPI returned an invalid response")
        articles = []
        for row in payload["articles"]:
            if not self._valid(row):
                continue
            try:
                articles.append(self._normalize(row))
            except (TypeError, ValueError):
                # One malformed upstream row must not discard the rest of a page.
                continue
        return articles

    @staticmethod
    def _valid(row: Any) -> bool:
        return isinstance(row, dict) and bool(row.get("title") and row.get("url") and row.get("publishedAt"))

    def _normalize(self, row: Dict[str, Any]) -> NormalizedArticle:
        url = str(row["url"])
        article_id = hashlib.sha256(f"newsapi:{url}".encode()).hexdigest()
        source = row.get("source") or {}
        return NormalizedArticle(
            id=article_id,
            provider=self.name,
            provider_article_id=article_id,
            source=str(source.get("name") or "NewsAPI"),
            title=str(row["title"]),
            description=str(row.get("description") or ""),
            content=str(row.get("content") or ""),
            url=url,
            published_at=datetime.fromisoformat(str(row["publishedAt"]).replace("Z", "+00:00")),
        )

    async def health(self) -> str:
        return "configured" if self.api_key else "not_configured"
