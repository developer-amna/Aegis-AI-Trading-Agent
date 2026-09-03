from market_data import MarketDataCollector
from debate_engine import DebateEngine
from alpaca_executor import AlpacaExecutionEngine


def run_pipeline():
    print("🚀 Starting Aegis Autonomous Trading Pipeline...\n")

    # 1. Fetch market data
    collector = MarketDataCollector()
    raw_payload = collector.fetch_stock_payload("AAPL")

    # Restructure data for DebateEngine
    sentiment_score = raw_payload.get("sentiment_score", 0.0)
    debate_input = {
        "symbol": raw_payload.get("symbol", "AAPL"),
        "market_data": {
            "current_price": raw_payload.get("price", 180.0),
            "rsi_14": raw_payload.get("rsi", 50.0),
            "macd_signal": "BULLISH",
            "volatility_index": 0.25,
        },
        "sentiment_data": {
            "news_headline_score": sentiment_score,
            "overall_sentiment": (
                "BULLISH" if sentiment_score > 0 else "BEARISH"
            ),
        },
    }

    print(f"📊 Market Data Fetched for {debate_input['symbol']}:")
    print(debate_input)

    # 2. Run multi-agent debate
    print("\n🤖 Initiating Multi-Agent Debate...")
    engine = DebateEngine()
    decision_schema = engine.evaluate_signals(debate_input)
    decision_dict = decision_schema.model_dump()

    # 3. Execute decision using Alpaca paper trading
    executor = AlpacaExecutionEngine()
    execution_result = executor.execute_decision(decision_dict, qty=1)

    print("\n" + "=" * 50)
    print("🏆 FINAL PIPELINE SUMMARY:")
    print(
        f"Asset: {decision_dict['symbol']} | "
        f"Decision: {decision_dict['action']} | "
        f"Order Status: {execution_result['status']}"
    )
    print("=" * 50)


if __name__ == "__main__":
    run_pipeline()