from debate_engine import DebateEngine

def test_pipeline_integration():
    print("🚀 Testing Task 4 Integration with Main Pipeline...")
    
    # Simulated Live Market Payload (as passed by Task 1 Orchestrator)
    incoming_payload = {
        "symbol": "NVDA",
        "market_data": {
            "current_price": 120.40,
            "rsi_14": 25.5,  # Oversold Signal
            "macd_signal": "BULLISH",
            "volatility_index": 0.32  # High Volatility Trigger
        },
        "sentiment_data": {
            "news_headline_score": 0.78,
            "overall_sentiment": "BULLISH"
        }
    }

    # Initialize Engine
    engine = DebateEngine()
    decision = engine.evaluate_signals(incoming_payload)

    # Verification Checks
    assert decision.symbol == "NVDA"
    assert decision.action in ["BUY", "SELL", "HOLD"]
    assert isinstance(decision.confidence, float)
    assert isinstance(decision.hedge_required, bool)

    print("\n✅ TASK 4 PIPELINE INTEGRATION TEST PASSED!")
    print(f"Ticker: {decision.symbol} | Action: {decision.action} | Confidence: {decision.confidence}")
    print(f"Hedge Needed: {decision.hedge_required}")
    print(f"Reasoning: {decision.reasoning}")

if __name__ == "__main__":
    test_pipeline_integration()