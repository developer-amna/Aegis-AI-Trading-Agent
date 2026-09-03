from types import SimpleNamespace

import pytest

from sentiment_service.app.schemas import ModelSentiment, SentimentLabel
from sentiment_service.app.sentiment import HybridSentimentEngine, SentimentEngine, SentimentEngineError, classify_score
from sentiment_service.app.sentiment.finbert import FinBERTEngine
from sentiment_service.app.sentiment.llm import LLMEngine


class Engine(SentimentEngine):
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error
    async def analyze(self, text, symbol):
        if self.error:
            raise self.error
        return self.result


@pytest.mark.asyncio
async def test_finbert_probability_weighted_scoring_without_model_download():
    engine = FinBERTEngine()
    engine._pipeline = lambda *args, **kwargs: [[
        {"label": "positive", "score": 0.80}, {"label": "negative", "score": 0.10}, {"label": "neutral", "score": 0.10}
    ]]
    result = await engine.analyze("Revenue beat expectations", "AAPL")
    assert result.sentiment == SentimentLabel.BULLISH
    assert result.score == pytest.approx(0.70)
    assert result.confidence == 0.80


@pytest.mark.asyncio
async def test_hybrid_uses_fallback_on_low_confidence_and_failure():
    low = ModelSentiment(sentiment="NEUTRAL", score=0.01, confidence=0.4, model="primary")
    backup = ModelSentiment(sentiment="BEARISH", score=-0.7, confidence=0.9, model="fallback")
    assert (await HybridSentimentEngine(Engine(low), Engine(backup), 0.55).analyze("x", "TSLA")).model == "fallback"
    assert (await HybridSentimentEngine(Engine(error=SentimentEngineError("down")), Engine(backup)).analyze("x", "TSLA")).score == -0.7


@pytest.mark.asyncio
async def test_llm_validates_and_normalizes_structured_response():
    message = SimpleNamespace(content='{"sentiment":"BEARISH","score":0.72,"confidence":0.88,"reason":"Earnings beat"}')
    create = lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=message)])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    result = await LLMEngine(None, "test", client=client).analyze("text", "AAPL")
    assert result.sentiment == SentimentLabel.BULLISH
    assert result.score == 0.72


@pytest.mark.asyncio
async def test_llm_rejects_invalid_output_after_retry():
    create = lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with pytest.raises(SentimentEngineError):
        await LLMEngine(None, "test", client=client).analyze("text", "AAPL")


def test_configurable_classification_thresholds():
    assert classify_score(0.19) == SentimentLabel.NEUTRAL
    assert classify_score(0.20) == SentimentLabel.BULLISH
    assert classify_score(-0.20) == SentimentLabel.BEARISH
