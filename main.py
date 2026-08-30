from market_data import MarketDataCollector
from debate_engine import DebateEngine
from alpaca_executor import AlpacaExecutionEngine

def run_pipeline():
    print("🚀 Starting Aegis Autonomous Trading Pipeline...\n")
    
    # 1. Fetch Market Data
    collector = MarketDataCollector()
    raw_payload = collector.fetch_stock_payload("AAPL")
    
    # 2. Execute Multi-Agent Debate Engine
    engine = DebateEngine()
    decision_schema = engine.run_debate(raw_payload)
    
    # Convert Pydantic Object to Dictionary
    decision_dict = decision_schema.model_dump()
    
    # 3. Execute Order on Alpaca Paper Trading Account
    executor = AlpacaExecutionEngine()
    execution_result = executor.execute_decision(decision_dict, qty=1)
    
    print("\n" + "="*50)
    print("🏆 FINAL PIPELINE SUMMARY:")
    print(f"Asset: {decision_dict['symbol']} | Decision: {decision_dict['action']} | Order Status: {execution_result['status']}")
    print("="*50)

if __name__ == "__main__":
    run_pipeline()