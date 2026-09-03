from __future__ import annotations

import re
from typing import Iterable

from ..schemas import NormalizedArticle


class FinancialRelevanceFilter:
    DEFAULT_TERMS = (
        "analyst", "bankruptcy", "bond", "buyback", "dividend", "earnings", "economy",
        "forecast", "guidance", "inflation", "interest rate", "investor", "market", "merger",
        "outlook", "profit", "revenue", "shares", "stock", "tariff", "valuation",
    )

    def __init__(self, terms: Iterable[str] = DEFAULT_TERMS):
        pattern = "|".join(re.escape(term) for term in terms)
        self._pattern = re.compile(rf"(?<!\w)(?:{pattern})(?!\w)", re.IGNORECASE)

    def is_relevant(self, article: NormalizedArticle) -> bool:
        return bool(self._pattern.search(f"{article.title} {article.content}"))

