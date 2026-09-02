import os
from typing import Dict, Any
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

load_dotenv()

class AlpacaExecutionEngine:
    def __init__(self):
        # Fetch Alpaca Paper Trading Credentials from .env
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        
        # Paper Trading Paper = True flag
        if self.api_key and self.secret_key:
            self.client = TradingClient(self.api_key, self.secret_key, paper=True)
            print("🟢 [Task 3: Alpaca Executor] Paper Trading Engine Connected.")
        else:
            self.client = None
            print("⚠️ [Task 3: Alpaca Executor] API Keys missing. Running in Simulation Mode.")

    def execute_decision(self, decision: Dict[str, Any], qty: int = 1) -> Dict[str, Any]:
        """
        Translates Aegis-AI Consensus Schema into Alpaca Order Execution
        """
        symbol = decision.get("symbol", "AAPL")
        action = decision.get("action", "HOLD").upper()
        confidence = decision.get("confidence", 0.0)
        hedge_required = decision.get("hedge_required", False)

        if action == "HOLD":
            print(f"⏸️ [Execution Skipped] Action is HOLD for {symbol}. No trade placed.")
            return {"status": "skipped", "reason": "HOLD action received"}

        if not self.client:
            print(f"🧪 [Simulated Order] {action} {qty} share(s) of {symbol} (Confidence: {confidence})")
            return {"status": "simulated", "symbol": symbol, "action": action, "qty": qty}

        try:
            # Map BUY / SELL actions
            order_side = OrderSide.BUY if action == "BUY" else OrderSide.SELL

            # Formulate Market Order
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )

            # Submit Order via Alpaca SDK
            order = self.client.submit_order(order_data=order_data)
            
            execution_log = {
                "status": "executed",
                "order_id": str(order.id),
                "symbol": order.symbol,
                "action": action,
                "qty": qty,
                "confidence": confidence,
                "hedge_flag_triggered": hedge_required
            }

            print(f"🚀 [Alpaca Live Order Success] {action} {qty} share(s) of {symbol} | Order ID: {order.id}")
            
            if hedge_required:
                print(f"🛡️ [Risk Hedge Signal] Volatility flag active for {symbol}. Protective Put option recommended.")

            return execution_log

        except Exception as e:
            print(f"❌ [Alpaca Execution Failed]: {str(e)}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Test Execution
    sample_decision = {
        "symbol": "AAPL",
        "action": "BUY",
        "confidence": 0.85,
        "hedge_required": False
    }
    
    executor = AlpacaExecutionEngine()
    response = executor.execute_decision(sample_decision, qty=2)
    print("\nExecution Response:")
    print(response)