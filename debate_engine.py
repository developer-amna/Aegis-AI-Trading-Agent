import json
from typing import Dict, Any, List, Tuple

from aegis_schemas import TradeDecision


class DebateEngine:
    """
    Multi-Agent Conflict Resolution Framework.
    Agents:
      1. Bullish Quant Agent (Growth focused)
      2. Bearish Risk Agent (Downside protection focused)
      3. Chief Investment Officer (CIO) Arbiter

    Expects a payload of the shape:
        {
            "symbol": str,
            "market_data": {
                "current_price": float,
                "rsi_14": float,
                "macd_signal": "BULLISH" | "BEARISH" | "NEUTRAL",
                "volatility_index": float
            },
            "sentiment_data": {
                "news_headline_score": float,
                "overall_sentiment": str
            },
            "risk_tolerance": int (1-10, optional, default 5)
        }
    (this is what MarketDataCollector.fetch_stock_payload() produces, and
    what app.py / main.py / test_integration.py all already build).

    Unlike a simple if/else engine, the confidence score and position size
    here are DERIVED from how many independent signals actually agree —
    not fixed constants — so the "consensus" claim is genuine.
    """

    def run_debate(self, payload: Dict[str, Any]) -> TradeDecision:
        symbol = payload.get("symbol", "AAPL")
        market = payload.get("market_data", {})
        sentiment = payload.get("sentiment_data", {})
        risk_tolerance = payload.get("risk_tolerance", 5)  # 1 (conservative) - 10 (aggressive)

        current_price = market.get("current_price", 0.0)
        rsi = market.get("rsi_14", 50.0)
        macd_signal = market.get("macd_signal", "NEUTRAL")
        volatility = market.get("volatility_index", 0.2)
        sentiment_score = sentiment.get("news_headline_score", 0.0)

        bull_signals, bear_signals = self._collect_signals(
            rsi, macd_signal, sentiment_score, current_price
        )
        bull_score, bear_score = len(bull_signals), len(bear_signals)

        action, confidence = self._decide(bull_score, bear_score)
        position_size_pct = self._size_position(action, confidence, risk_tolerance)
        hedge_required = self._needs_hedge(volatility, bull_score, bear_score, action)

        bull_case = self._compose_case(
            bull_signals,
            fallback=f"No strong bullish signals detected for {symbol} at ${current_price} right now."
        )
        bear_case = self._compose_case(
            bear_signals,
            fallback=f"No strong bearish signals detected for {symbol}; downside risk looks contained."
        )
        reasoning = self._compose_reasoning(action, bull_score, bear_score, confidence, hedge_required)

        return TradeDecision(
            symbol=symbol,
            action=action,
            confidence=confidence,
            hedge_required=hedge_required,
            reasoning=reasoning,
            bull_case=bull_case,
            bear_case=bear_case,
            position_size_pct=position_size_pct,
        )

    # Alias so callers using either name keep working (test_integration.py
    # calls evaluate_signals(); app.py and main.py call run_debate()).
    def evaluate_signals(self, payload: Dict[str, Any]) -> TradeDecision:
        return self.run_debate(payload)

    # ------------------------------------------------------------------
    # Signal collection — each signal is (reason_text) added independently,
    # so confidence reflects how many independent factors actually agree.
    # ------------------------------------------------------------------
    def _collect_signals(
        self, rsi: float, macd_signal: str, sentiment_score: float, current_price: float
    ) -> Tuple[List[str], List[str]]:
        bull_signals: List[str] = []
        bear_signals: List[str] = []

        if rsi < 30:
            bull_signals.append(f"RSI at {rsi} is deeply oversold — historically a strong reversal zone.")
        elif rsi < 40:
            bull_signals.append(f"RSI at {rsi} is approaching oversold territory, favoring accumulation.")

        if rsi > 70:
            bear_signals.append(f"RSI at {rsi} is deeply overbought — correction risk is elevated.")
        elif rsi > 65:
            bear_signals.append(f"RSI at {rsi} is stretched to the upside, raising pullback risk.")

        if macd_signal == "BULLISH":
            bull_signals.append("MACD histogram confirms bullish momentum on the trend.")
        elif macd_signal == "BEARISH":
            bear_signals.append("MACD histogram confirms bearish momentum on the trend.")

        if sentiment_score > 0.4:
            bull_signals.append(f"News sentiment score of {sentiment_score} is strongly positive.")
        elif sentiment_score > 0.15:
            bull_signals.append(f"News sentiment score of {sentiment_score} leans positive.")

        if sentiment_score < -0.4:
            bear_signals.append(f"News sentiment score of {sentiment_score} is strongly negative.")
        elif sentiment_score < -0.15:
            bear_signals.append(f"News sentiment score of {sentiment_score} leans negative.")

        return bull_signals, bear_signals

    # ------------------------------------------------------------------
    # Consensus logic — confidence scales with how many signals agree,
    # instead of being a fixed 0.88 / 0.82 / 0.65.
    # ------------------------------------------------------------------
    def _decide(self, bull_score: int, bear_score: int) -> Tuple[str, float]:
        if bull_score > bear_score:
            action = "BUY"
            confidence = min(0.95, 0.55 + 0.13 * bull_score)
        elif bear_score > bull_score:
            action = "SELL"
            confidence = min(0.95, 0.55 + 0.13 * bear_score)
        else:
            action = "HOLD"
            # Some agreement on both sides still nudges confidence up slightly
            confidence = round(min(0.70, 0.55 + 0.03 * (bull_score + bear_score)), 2)
        return action, round(confidence, 2)

    # ------------------------------------------------------------------
    # Position sizing — scales with both confidence AND the trader's own
    # risk tolerance (1-10 slider in the dashboard), not a flat 10%.
    # ------------------------------------------------------------------
    def _size_position(self, action: str, confidence: float, risk_tolerance: int) -> int:
        if action == "HOLD":
            return 0
        risk_tolerance = max(1, min(10, risk_tolerance))
        # Max ~25% of portfolio at full confidence + max risk tolerance
        raw_size = confidence * (risk_tolerance / 10) * 25
        return int(round(raw_size))

    # ------------------------------------------------------------------
    # Hedge logic — triggers on elevated volatility OR when the CIO is
    # acting against some conflicting evidence (mixed signals).
    # ------------------------------------------------------------------
    def _needs_hedge(self, volatility: float, bull_score: int, bear_score: int, action: str) -> bool:
        if volatility >= 0.28:
            return True
        if action == "BUY" and bear_score >= 1:
            return True
        if action == "SELL" and bull_score >= 1:
            return True
        return False

    # ------------------------------------------------------------------
    # Text composition helpers
    # ------------------------------------------------------------------
    def _compose_case(self, signals: List[str], fallback: str) -> str:
        return " ".join(signals) if signals else fallback

    def _compose_reasoning(
        self, action: str, bull_score: int, bear_score: int, confidence: float, hedge_required: bool
    ) -> str:
        agree_note = f"{bull_score} bullish vs {bear_score} bearish signal(s) considered"
        hedge_note = " A hedge is recommended given the conflicting/volatile setup." if hedge_required else ""

        if action == "BUY":
            return f"Bullish signals outweigh bearish ones ({agree_note}) — consensus confidence {int(confidence*100)}%.{hedge_note}"
        elif action == "SELL":
            return f"Bearish signals outweigh bullish ones ({agree_note}) — consensus confidence {int(confidence*100)}%.{hedge_note}"
        else:
            return f"Signals are balanced or too weak to act on ({agree_note}) — standing by for a clearer trend.{hedge_note}"


if __name__ == "__main__":
    sample_payload = {
        "symbol": "AAPL",
        "market_data": {
            "current_price": 185.50,
            "rsi_14": 28.0,
            "macd_signal": "BULLISH",
            "volatility_index": 0.25,
        },
        "sentiment_data": {
            "news_headline_score": 0.6,
            "overall_sentiment": "BULLISH",
        },
        "risk_tolerance": 7,
    }
    engine = DebateEngine()
    result = engine.run_debate(sample_payload)
    print(json.dumps(result.model_dump(), indent=2))