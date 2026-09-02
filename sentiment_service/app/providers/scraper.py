from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .base import NewsProvider, ProviderError
from ..schemas import NormalizedArticle


class RSSScraperProvider(NewsProvider):
    """Ingests configured public RSS/Atom feeds and extracts linked article text.

    Operators are responsible for listing only feeds whose terms and robots policy
    permit automated access. No feeds are enabled by default.
    """

    name = "rss_scraper"

    def __init__(self, feed_urls: List[str], client: Optional[httpx.AsyncClient] = None):
        self.feed_urls = feed_urls
        self._client = client

    async def fetch(self, since: datetime, symbols: Optional[List[str]] = None) -> List[NormalizedArticle]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers={"User-Agent": "AegisSentimentBot/1.0"})
        articles: List[NormalizedArticle] = []
        try:
            for feed_url in self.feed_urls:
                try:
                    response = await client.get(feed_url)
                    response.raise_for_status()
                    entries = self._entries(response.text)
                    for entry in entries:
                        if entry["published_at"] < since:
                            continue
                        content = await self._extract_page(client, entry["url"])
                        articles.append(self._normalize(feed_url, entry, content))
                except (httpx.HTTPError, ET.ParseError, ValueError):
                    continue
        finally:
            if own_client:
                await client.aclose()
        return articles

    def _entries(self, xml_text: str) -> List[dict]:
        root = ET.fromstring(xml_text)
        result = []
        nodes = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        for node in nodes:
            title = self._text(node, "title")
            link = self._text(node, "link")
            if not link:
                link_node = node.find("{http://www.w3.org/2005/Atom}link")
                link = link_node.attrib.get("href", "") if link_node is not None else ""
            date_raw = self._text(node, "pubDate") or self._text(node, "published") or self._text(node, "updated")
            description = self._text(node, "description") or self._text(node, "summary")
            if not title or not link or not date_raw:
                continue
            try:
                published = parsedate_to_datetime(date_raw) if "," in date_raw else datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
            except (TypeError, ValueError):
                continue
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            result.append({"title": title, "url": link, "description": description, "published_at": published.astimezone(timezone.utc)})
        return result

    @staticmethod
    def _text(node: ET.Element, local_name: str) -> str:
        for child in node.iter():
            if child.tag.rsplit("}", 1)[-1] == local_name and child.text:
                return child.text.strip()
        return ""

    async def _extract_page(self, client: httpx.AsyncClient, url: str) -> str:
        try:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["script", "style", "nav", "footer", "aside", "form"]):
                element.decompose()
            article = soup.find("article") or soup.find("main") or soup.body
            return article.get_text(" ", strip=True) if article else ""
        except httpx.HTTPError:
            return ""

    def _normalize(self, feed_url: str, entry: dict, content: str) -> NormalizedArticle:
        article_id = hashlib.sha256(f"rss:{entry['url']}".encode()).hexdigest()
        source = urlparse(feed_url).netloc.lower().removeprefix("www.")
        return NormalizedArticle(
            id=article_id,
            provider=self.name,
            provider_article_id=article_id,
            source=source,
            title=entry["title"],
            description=re.sub(r"<[^>]+>", " ", entry["description"]),
            content=content,
            url=entry["url"],
            published_at=entry["published_at"],
        )

    async def health(self) -> str:
        return "configured" if self.feed_urls else "not_configured"
