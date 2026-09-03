from datetime import datetime, timezone

import pytest

from sentiment_service.app.processing import ArticleCleaner, ArticleDeduplicator, EntityExtractor, InvalidArticleError
from sentiment_service.app.schemas import NormalizedArticle


def article(**updates):
    values = dict(
        id="a1", provider="fixture", provider_article_id="p1", source="Wire",
        title="Apple beats estimates but lowers future guidance",
        description="<p>Apple Inc. posted <b>strong</b> revenue.</p>",
        content="Demand improved.  Demand improved. Guidance was lowered because costs rose.",
        url="https://example.test/story?utm_source=x", published_at=datetime.now(timezone.utc),
    )
    values.update(updates)
    return NormalizedArticle(**values)


def test_cleaner_preserves_mixed_financial_language_and_removes_html_duplicates():
    cleaned = ArticleCleaner(min_chars=20).clean(article())
    assert "beats estimates" in cleaned.title
    assert "lowers future guidance" in cleaned.title
    assert "<p>" not in cleaned.content
    assert cleaned.content.count("Demand improved") == 1


def test_cleaner_removes_publisher_preference_boilerplate_that_causes_false_tickers():
    value = article(
        title="Central banks discuss inflation",
        description="Officials reviewed interest rates and the economic outlook.",
        content="Policy makers discussed inflation risks. Choose CNBC as your preferred source on Google and never miss a moment.",
    )
    cleaned = ArticleCleaner(min_chars=20).clean(value)
    assert "Google" not in cleaned.content


def test_cleaner_rejects_empty_and_truncates_long_content():
    with pytest.raises(InvalidArticleError):
        ArticleCleaner(min_chars=20).clean(article(title="", description="", content=""))
    cleaned = ArticleCleaner(min_chars=10, max_chars=100).clean(article(content="word " * 1000))
    assert len(f"{cleaned.title}. {cleaned.content}") <= 100


def test_entity_extraction_is_conservative():
    extractor = EntityExtractor({"AAPL": ("Apple", "Apple Inc."), "NVDA": ("NVIDIA",)})
    assert extractor.extract(article())[0][0] == "AAPL"
    assert extractor.extract(article(title="The economy slowed", description="", content="No named company.")) == []


def test_dedup_url_id_hash_and_similar_headline(repository):
    dedup = ArticleDeduplicator(repository)
    base = article(url=dedup.normalize_url(article().url))
    hashed = base.model_copy(update={"article_hash": dedup.identify(base)})
    repository.save_article(hashed, {"AAPL": 0.9})
    assert dedup.is_duplicate(article(provider_article_id="different"))  # same normalized URL/hash
    assert dedup.is_duplicate(article(id="a2", url="https://other.test", content="different", title="Apple beats estimates, but lowers future guidance!"))
    distinct = article(id="a3", provider_article_id="p3", url="https://new.test", title="NVIDIA opens a new research facility", content="Unique details about a large new laboratory.")
    assert not dedup.is_duplicate(distinct)


def test_dedup_provider_id_and_content_hash_independently(repository):
    dedup = ArticleDeduplicator(repository)
    base = article(url="https://one.test/story")
    base = base.model_copy(update={"article_hash": dedup.identify(base)})
    repository.save_article(base, {"AAPL": 0.9})
    same_id = article(id="a2", url="https://two.test/story", content="different body", title="Different title")
    assert dedup.is_duplicate(same_id)
    same_hash = article(id="a3", provider_article_id="p3", url="https://three.test/story")
    assert dedup.is_duplicate(same_hash)
