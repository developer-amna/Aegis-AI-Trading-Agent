from __future__ import annotations

import re
from typing import Dict, Iterable, List, Sequence, Tuple

from ..schemas import NormalizedArticle


class EntityExtractor:
    def __init__(self, company_mapping: Dict[str, Sequence[str]]):
        self.company_mapping = {key.upper(): tuple(names) for key, names in company_mapping.items()}

    def extract(self, article: NormalizedArticle) -> List[Tuple[str, str, float]]:
        text = f"{article.title} {article.description} {article.content}"
        entities: Dict[str, Tuple[str, float]] = {}
        explicit = set(re.findall(r"(?<![A-Z0-9])\$?([A-Z]{1,5})(?![A-Z0-9])", text))
        for symbol in explicit.intersection(self.company_mapping):
            entities[symbol] = (self.company_mapping[symbol][0], 1.0)
        lower_text = text.casefold()
        for symbol, names in self.company_mapping.items():
            for name in names:
                if re.search(rf"(?<!\w){re.escape(name.casefold())}(?!\w)", lower_text):
                    old = entities.get(symbol)
                    entities[symbol] = (name, max(old[1] if old else 0.0, 0.9))
                    break
        return [(symbol, company, confidence) for symbol, (company, confidence) in sorted(entities.items())]

    def enrich(self, article: NormalizedArticle) -> NormalizedArticle:
        entities = self.extract(article)
        return article.model_copy(update={
            "symbols": [entity[0] for entity in entities],
            "company_names": [entity[1] for entity in entities],
        })

    def is_supported(self, symbol: str) -> bool:
        return symbol.upper() in self.company_mapping
