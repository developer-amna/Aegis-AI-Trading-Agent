from market_data import MarketDataCollector
from debate_engine import DebateEngine

def run_pipeline():
    print("🚀 Starting Aegis Trading Agent Pipeline...\n")
    
    # 1. Task 1: Fetch Market Data
    collector = MarketDataCollector()
    raw_payload = collector.fetch_stock_payload("AAPL")
    
    # Restructure payload for DebateEngine input schema
    debate_input = {
        "symbol": raw_payload.get("symbol", "AAPL"),
        "market_data": {
            "current_price": raw_payload.get("price", 180.0),
            "rsi_14": raw_payload.get("rsi", 50.0),
            "macd_signal": "BULLISH",
            "volatility_index": 0.25
        },
        "sentiment_data": {
            "news_headline_score": raw_payload.get("sentiment_score", 0.5),
            "overall_sentiment": "BULLISH"
        }
    }

    print(f"📊 Market Data Fetched for {debate_input['symbol']}:")
    print(debate_input)
    print("\n" + "="*40 + "\n")

    # 2. Task 4: Execute Debate Engine with evaluate_signals
    print("🤖 Initiating Multi-Agent Debate...")
    engine = DebateEngine()
    
    # Correct function call: evaluate_signals instead of run_debate
    decision_schema = engine.evaluate_signals(debate_input)

    print("\n" + "="*40 + "\n")
    print(f"🎯 Final Execution Decision for {debate_input['symbol']}:")
    print(decision_schema.model_dump_json(indent=2))

if __name__ == "__main__":
    run_pipeline()