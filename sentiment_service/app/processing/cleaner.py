from __future__ import annotations

import html
import re
import unicodedata

from bs4 import BeautifulSoup

from ..schemas import NormalizedArticle


class InvalidArticleError(ValueError):
    pass


class ArticleCleaner:
    BOILERPLATE = (
        r"sign up for (?:our|the) newsletter.*$",
        r"click here to (?:read|subscribe).*$",
        r"choose .{0,100} as your preferred source on google.*$",
        r"all rights reserved.*$",
    )

    def __init__(self, min_chars: int = 80, max_chars: int = 12000):
        self.min_chars = min_chars
        self.max_chars = max_chars

    def clean(self, article: NormalizedArticle) -> NormalizedArticle:
        title = self.clean_text(article.title)
        body = self.clean_text(" ".join(filter(None, [article.description, article.content])))
        for pattern in self.BOILERPLATE:
            body = re.sub(pattern, "", body, flags=re.IGNORECASE | re.DOTALL).strip()
        body = self._remove_repeated_sentences(body)
        combined = f"{title}. {body}".strip()
        if len(combined) < self.min_chars:
            raise InvalidArticleError("article content is too short")
        if len(combined) > self.max_chars:
            body = body[: max(0, self.max_chars - len(title) - 2)].rsplit(" ", 1)[0]
        return article.model_copy(update={"title": title, "description": "", "content": body})

    @staticmethod
    def clean_text(value: str) -> str:
        soup = BeautifulSoup(html.unescape(value or ""), "html.parser")
        text = soup.get_text(" ", strip=True)
        text = unicodedata.normalize("NFKC", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _remove_repeated_sentences(value: str) -> str:
        seen = set()
        output = []
        for sentence in re.split(r"(?<=[.!?])\s+", value):
            key = re.sub(r"\W+", " ", sentence).strip().lower()
            if key and key not in seen:
                seen.add(key)
                output.append(sentence)
        return " ".join(output)
