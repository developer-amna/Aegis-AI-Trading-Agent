from __future__ import annotations

from pathlib import Path

import pytest

from sentiment_service.app.repository import SentimentRepository


@pytest.fixture
def repository(tmp_path: Path):
    repo = SentimentRepository(tmp_path / "sentiment-test.db")
    repo.initialize()
    yield repo
    repo.close()

