"""Minimal read-only Orchestrator integration example."""
import os

import httpx


def get_sentiment(symbol: str) -> dict:
    base_url = os.getenv("SENTIMENT_SERVICE_URL", "http://127.0.0.1:8000")
    headers = {}
    if os.getenv("SENTIMENT_SERVICE_API_KEY"):
        headers["X-API-Key"] = os.environ["SENTIMENT_SERVICE_API_KEY"]
    response = httpx.get(f"{base_url}/api/v1/sentiment/{symbol.upper()}", headers=headers, timeout=5.0)
    response.raise_for_status()
    result = response.json()
    # The Orchestrator should gate on freshness/confidence before using the signal.
    if result["data_status"] != "FRESH" or result["confidence"] == 0:
        return {"usable": False, "sentiment": result}
    return {"usable": True, "sentiment": result}


if __name__ == "__main__":
    print(get_sentiment("AAPL"))

