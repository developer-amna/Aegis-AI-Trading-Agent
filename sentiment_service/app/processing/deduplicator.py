from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from typing import Iterable, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..schemas import NormalizedArticle


class ArticleDeduplicator:
    def __init__(self, repository, headline_similarity: float = 0.92):
        self.repository = repository
        self.headline_similarity = headline_similarity

    @staticmethod
    def normalize_url(url: str) -> str:
        parts = urlsplit(url)
        query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_")]
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))

    @staticmethod
    def normalize_headline(title: str) -> str:
        return re.sub(r"[^a-z0-9 ]+", "", re.sub(r"\s+", " ", title.lower())).strip()

    @classmethod
    def content_hash(cls, article: NormalizedArticle) -> str:
        basis = re.sub(r"\s+", " ", f"{article.title} {article.content}".lower()).strip()
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()

    def identify(self, article: NormalizedArticle) -> str:
        return self.content_hash(article)

    def is_duplicate(self, article: NormalizedArticle, recent_headlines: Optional[Iterable[str]] = None) -> bool:
        content_hash = self.identify(article)
        if self.repository.article_exists(
            provider=article.provider,
            provider_article_id=article.provider_article_id,
            url=self.normalize_url(article.url),
            content_hash=content_hash,
        ):
            return True
        normalized = self.normalize_headline(article.title)
        candidates = list(recent_headlines or self.repository.recent_headlines(limit=250))
        return any(SequenceMatcher(None, normalized, self.normalize_headline(candidate)).ratio() >= self.headline_similarity for candidate in candidates)

