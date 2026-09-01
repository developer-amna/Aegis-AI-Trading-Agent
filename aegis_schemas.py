"""
Unified schema for Aegis AI Trading Agent.

Every module (debate_engine.py, alpaca_executor.py, app.py, main.py,
test_integration.py) should import TradeDecision from here instead of
building its own dict/object shape. This is the single source of truth
for what a "decision" looks like across the whole pipeline.
"""

from pydantic import BaseModel, Field


class TradeDecision(BaseModel):
    symbol: str
    action: str = Field(description="One of: BUY, SELL, HOLD")
    confidence: float = Field(ge=0.0, le=1.0)
    hedge_required: bool
    reasoning: str
    bull_case: str
    bear_case: str
    position_size_pct: int = 0