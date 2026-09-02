from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import SentimentEngine, SentimentEngineError, classify_score
from ..schemas import ModelSentiment, SentimentLabel


class LLMResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sentiment: SentimentLabel
    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=500)


class LLMEngine(SentimentEngine):
    name = "llm"

    def __init__(self, api_key: Optional[str], model: str, base_url: Optional[str] = None, client: Any = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = client

    def available(self) -> bool:
        return bool(self.api_key or self._client)

    def _client_instance(self) -> Any:
        if self._client:
            return self._client
        if not self.api_key:
            raise SentimentEngineError("LLM fallback is not configured")
        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            return self._client
        except Exception as exc:
            raise SentimentEngineError(f"LLM client unavailable: {exc}") from exc

    def _invoke(self, text: str, symbol: str) -> ModelSentiment:
        prompt = (
            "Analyze only the financial impact of this news on the given security. "
            "Return strict JSON with sentiment (BULLISH, BEARISH, or NEUTRAL), score (-1 to 1), "
            "confidence (0 to 1), and a concise reason. Do not recommend a trade.\n"
            f"Symbol: {symbol}\nArticle: {text}"
        )
        client = self._client_instance()
        last_error: Optional[Exception] = None
        formats = [
            {
                "type": "json_schema",
                "json_schema": {
                    "name": "financial_sentiment",
                    "strict": True,
                    "schema": LLMResult.model_json_schema(),
                },
            },
            {"type": "json_object"},  # Compatibility fallback for non-OpenAI endpoints.
        ]
        for response_format in formats:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    temperature=0,
                    response_format=response_format,
                    messages=[{"role": "system", "content": "You are a financial sentiment classifier."}, {"role": "user", "content": prompt}],
                )
                content = response.choices[0].message.content
                parsed = LLMResult.model_validate(json.loads(content))
                computed_label = classify_score(parsed.score)
                if parsed.sentiment != computed_label:
                    parsed = parsed.model_copy(update={"sentiment": computed_label})
                return ModelSentiment(**parsed.model_dump(), model=self.model)
            except Exception as exc:
                last_error = exc
        raise SentimentEngineError(f"LLM analysis failed or returned invalid structured output: {last_error}")

    async def analyze(self, text: str, symbol: str) -> ModelSentiment:
        return await asyncio.to_thread(self._invoke, text, symbol)
