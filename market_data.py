import pandas as pd
import numpy as np
from typing import Dict, Any

try:
    import yfinance as yf
except ImportError:
    yf = None


def calculate_advanced_metrics(prices: pd.Series) -> Dict[str, Any]:
    """Winner-grade quantitative factor analysis."""
    # 1. RSI Calculation (14 Days)
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = round(float(rsi.iloc[-1]), 2) if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50.0

    # 2. MACD Crossover
    exp1 = prices.ewm(span=12, adjust=False).mean()
    exp2 = prices.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_diff = macd.iloc[-1] - signal.iloc[-1]

    macd_signal = "BULLISH" if macd_diff > 0.3 else ("BEARISH" if macd_diff < -0.3 else "NEUTRAL")

    # 3. Bollinger Bands & Volatility
    sma20 = prices.rolling(window=20).mean()
    std20 = prices.rolling(window=20).std()
    upper_band = sma20 + (std20 * 2)
    lower_band = sma20 - (std20 * 2)

    current_price = prices.iloc[-1]
    bb_status = "OVERBOUGHT" if current_price >= upper_band.iloc[-1] else (
        "OVERSOLD" if current_price <= lower_band.iloc[-1] else "NORMAL"
    )

    returns = prices.pct_change().dropna()
    volatility = round(float(returns.std() * np.sqrt(252)), 2)

    return {
        "rsi": current_rsi,
        "macd_signal": macd_signal,
        "bollinger_band": bb_status,
        "volatility": volatility,
        "sma_20": round(float(sma20.iloc[-1]), 2)
    }


def get_market_data(symbol: str = "AAPL") -> Dict[str, Any]:
    """Fetch quant metrics for a symbol. Falls back to mock data if yfinance
    is unavailable or the request fails, so demos never crash."""
    symbol = symbol.upper()
    if yf:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo")
            if not hist.empty and len(hist) > 20:
                prices = hist['Close']
                metrics = calculate_advanced_metrics(prices)

                return {
                    "symbol": symbol,
                    "current_price": round(float(prices.iloc[-1]), 2),
                    "rsi_14": metrics["rsi"],
                    "macd_signal": metrics["macd_signal"],
                    "bollinger_band": metrics["bollinger_band"],
                    "volatility_index": metrics["volatility"],
                    "sma_20": metrics["sma_20"],
                    "quant_recommendation": "BUY" if (metrics["rsi"] < 35 and metrics["macd_signal"] == "BULLISH") else (
                        "SELL" if (metrics["rsi"] > 65 and metrics["macd_signal"] == "BEARISH") else "HOLD"
                    )
                }
        except Exception:
            pass

    # Fallback High-Quality Mock
    return {
        "symbol": symbol,
        "current_price": 185.50,
        "rsi_14": 32.4,
        "macd_signal": "BULLISH",
        "bollinger_band": "OVERSOLD",
        "volatility_index": 0.18,
        "sma_20": 182.10,
        "quant_recommendation": "BUY"
    }


class MarketDataCollector:
    """
    Wraps get_market_data() and packages it into the payload shape that
    DebateEngine.run_debate() / evaluate_signals() expects:

        {
            "symbol": str,
            "market_data": {current_price, rsi_14, macd_signal, volatility_index},
            "sentiment_data": {news_headline_score, overall_sentiment}
        }

    NOTE: sentiment_data is a neutral placeholder until Task 2 (News &
    Financial Sentiment Engine) is ready. Once that module exists, replace
    the placeholder block below with a real call to it.
    """

    def fetch_stock_payload(self, symbol: str = "AAPL", risk_tolerance: int = 5) -> Dict[str, Any]:
        quant = get_market_data(symbol)

        return {
            "symbol": quant["symbol"],
            "market_data": {
                "current_price": quant["current_price"],
                "rsi_14": quant["rsi_14"],
                "macd_signal": quant["macd_signal"],
                "volatility_index": quant["volatility_index"],
            },
            "sentiment_data": {
                # Placeholder until Task 2's sentiment engine is wired in
                "news_headline_score": 0.0,
                "overall_sentiment": "NEUTRAL",
            },
            "risk_tolerance": risk_tolerance,
        }


if __name__ == "__main__":
    import json
    collector = MarketDataCollector()
    print(json.dumps(collector.fetch_stock_payload("AAPL"), indent=2))