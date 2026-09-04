import os
import streamlit as st
from typing import Dict, Any
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

load_dotenv()


class AlpacaExecutionEngine:
    def __init__(self):
        # Fetch Alpaca Paper Trading Credentials from .env
        self.api_key = st.secrets.get("ALPACA_API_KEY", os.getenv("ALPACA_API_KEY"))
        self.secret_key = st.secrets.get("ALPACA_SECRET_KEY", os.getenv("ALPACA_SECRET_KEY"))

        # Paper Trading
        if self.api_key and self.secret_key:
            self.client = TradingClient(
                self.api_key,
                self.secret_key,
                paper=True
            )

            print("🟢 [Task 3: Alpaca Executor] Paper Trading Engine Connected.")

            # ---------------------------------------------------------
            # Verify API Key + Secret Key
            # ---------------------------------------------------------
            try:
                account = self.client.get_account()

                print("✅ API KEY + SECRET KEY VERIFIED SUCCESSFULLY")
                print(f"✅ Paper Account Status: {account.status}")
                print(f"✅ Buying Power: ${account.buying_power}")

            except Exception as e:
                print("❌ API KEY / SECRET KEY VERIFICATION FAILED")
                print(f"Error: {e}")

        else:
            self.client = None
            print(
                "⚠️ [Task 3: Alpaca Executor] "
                "API Keys missing. Running in Simulation Mode."
            )

    def execute_decision(
        self,
        decision: Dict[str, Any],
        qty: int = 1
    ) -> Dict[str, Any]:
        """
        Translates Aegis-AI Consensus Schema
        into Alpaca Paper Order Execution.
        """

        symbol = decision.get("symbol", "AAPL")
        action = decision.get("action", "HOLD").upper()
        confidence = decision.get("confidence", 0.0)
        hedge_required = decision.get("hedge_required", False)

        # ---------------------------------------------------------
        # HOLD = No Order
        # ---------------------------------------------------------
        if action == "HOLD":
            print(
                f"⏸️ [Execution Skipped] "
                f"Action is HOLD for {symbol}. No trade placed."
            )

            return {
                "status": "skipped",
                "reason": "HOLD action received"
            }

        # ---------------------------------------------------------
        # Simulation Mode if API credentials are missing
        # ---------------------------------------------------------
        if not self.client:
            print(
                f"🧪 [Simulated Order] "
                f"{action} {qty} share(s) of {symbol} "
                f"(Confidence: {confidence})"
            )

            return {
                "status": "simulated",
                "symbol": symbol,
                "action": action,
                "qty": qty
            }

        try:
            # ---------------------------------------------------------
            # Map BUY / SELL actions
            # ---------------------------------------------------------
            order_side = (
                OrderSide.BUY
                if action == "BUY"
                else OrderSide.SELL
            )

            # ---------------------------------------------------------
            # Create Market Order
            # ---------------------------------------------------------
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )

            # ---------------------------------------------------------
            # Submit Order through Alpaca Paper Trading API
            # ---------------------------------------------------------
            order = self.client.submit_order(
                order_data=order_data
            )

            execution_log = {
                "status": "executed",
                "order_id": str(order.id),
                "symbol": order.symbol,
                "action": action,
                "qty": qty,
                "confidence": confidence,
                "hedge_flag_triggered": hedge_required
            }

            print(
                f"🚀 [Alpaca Paper Order Success] "
                f"{action} {qty} share(s) of {symbol} "
                f"| Order ID: {order.id}"
            )

            # ---------------------------------------------------------
            # Hedge Signal
            # ---------------------------------------------------------
            if hedge_required:
                print(
                    f"🛡️ [Risk Hedge Signal] "
                    f"Volatility flag active for {symbol}. "
                    f"Protective Put option recommended."
                )

            return execution_log

        except Exception as e:
            print(
                f"❌ [Alpaca Execution Failed]: {str(e)}"
            )

            return {
                "status": "error",
                "message": str(e)
            }


# ============================================================================
# TEST EXECUTION
# ============================================================================

if __name__ == "__main__":

    sample_decision = {
        "symbol": "AAPL",
        "action": "BUY",
        "confidence": 0.85,
        "hedge_required": False
    }

    executor = AlpacaExecutionEngine()

    response = executor.execute_decision(
        sample_decision,
        qty=2
    )

    print("\nExecution Response:")
    print(response)