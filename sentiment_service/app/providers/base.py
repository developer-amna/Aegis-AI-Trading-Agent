from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..schemas import NormalizedArticle


class ProviderError(RuntimeError):
    """A recoverable upstream provider failure."""


class ProviderRateLimitError(ProviderError):
    """An upstream provider rejected the request due to rate limiting."""


class NewsProvider(ABC):
    name: str

    @abstractmethod
    async def fetch(self, since: datetime, symbols: Optional[List[str]] = None) -> List[NormalizedArticle]:
        """Return normalized articles published on or after ``since``."""

    async def health(self) -> str:
        return "configured"

