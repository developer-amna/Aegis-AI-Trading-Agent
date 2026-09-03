from dataclasses import dataclass
from typing import Optional


# ==========================================
# RISK MANAGEMENT CONFIGURATION
# ==========================================

MAX_CAPITAL_ALLOCATION = 0.02       # Maximum 2% per trade
STOP_LOSS_PERCENT = 0.015           # 1.5% mandatory stop-loss
DAILY_DRAWDOWN_LIMIT = 0.03         # Maximum 3% daily drawdown


# ==========================================
# TRADE REQUEST
# ==========================================

@dataclass
class TradeRequest:
    symbol: str
    action: str
    entry_price: float
    quantity: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


# ==========================================
# PORTFOLIO INFORMATION
# ==========================================

@dataclass
class PortfolioState:
    total_equity: float
    starting_daily_equity: float


# ==========================================
# RISK DECISION
# ==========================================

@dataclass
class RiskDecision:
    approved: bool
    reason: str
    position_value: float
    stop_loss: Optional[float]
    take_profit: Optional[float]


# ==========================================
# RISK MANAGER
# ==========================================

class RiskManager:

    def __init__(self):
        self.max_capital_allocation = MAX_CAPITAL_ALLOCATION
        self.stop_loss_percent = STOP_LOSS_PERCENT
        self.daily_drawdown_limit = DAILY_DRAWDOWN_LIMIT

    def validate_trade(
        self,
        trade: TradeRequest,
        portfolio: PortfolioState
    ) -> RiskDecision:

        # --------------------------------------
        # 1. Validate trading action
        # --------------------------------------

        if trade.action not in {"BUY", "SELL"}:
            return RiskDecision(
                approved=False,
                reason="Trade rejected: action must be BUY or SELL.",
                position_value=0,
                stop_loss=trade.stop_loss,
                take_profit=trade.take_profit
            )

        # --------------------------------------
        # 2. Basic input validation
        # --------------------------------------

        if trade.entry_price <= 0:
            return RiskDecision(
                approved=False,
                reason="Entry price must be greater than zero.",
                position_value=0,
                stop_loss=None,
                take_profit=None
            )

        if trade.quantity <= 0:
            return RiskDecision(
                approved=False,
                reason="Trade quantity must be greater than zero.",
                position_value=0,
                stop_loss=None,
                take_profit=None
            )

        if portfolio.total_equity <= 0:
            return RiskDecision(
                approved=False,
                reason="Portfolio equity must be greater than zero.",
                position_value=0,
                stop_loss=None,
                take_profit=None
            )

        if portfolio.starting_daily_equity <= 0:
            return RiskDecision(
                approved=False,
                reason="Starting daily equity must be greater than zero.",
                position_value=0,
                stop_loss=None,
                take_profit=None
            )

        # --------------------------------------
        # 3. Calculate position value
        # --------------------------------------

        position_value = trade.entry_price * trade.quantity

        # --------------------------------------
        # 4. Validate user-provided stop-loss
        # --------------------------------------

        if trade.stop_loss is not None:

            if trade.action == "BUY" and trade.stop_loss >= trade.entry_price:
                return RiskDecision(
                    approved=False,
                    reason=(
                        "Trade rejected: BUY stop-loss "
                        "must be below entry price."
                    ),
                    position_value=position_value,
                    stop_loss=trade.stop_loss,
                    take_profit=trade.take_profit
                )

            if trade.action == "SELL" and trade.stop_loss <= trade.entry_price:
                return RiskDecision(
                    approved=False,
                    reason=(
                        "Trade rejected: SELL stop-loss "
                        "must be above entry price."
                    ),
                    position_value=position_value,
                    stop_loss=trade.stop_loss,
                    take_profit=trade.take_profit
                )

        # --------------------------------------
        # 5. Validate take-profit
        # --------------------------------------

        if trade.take_profit is None:
            return RiskDecision(
                approved=False,
                reason="Trade blocked: take-profit level is required.",
                position_value=position_value,
                stop_loss=trade.stop_loss,
                take_profit=None
            )

        if trade.action == "BUY" and trade.take_profit <= trade.entry_price:
            return RiskDecision(
                approved=False,
                reason=(
                    "Trade rejected: BUY take-profit "
                    "must be above entry price."
                ),
                position_value=position_value,
                stop_loss=trade.stop_loss,
                take_profit=trade.take_profit
            )

        if trade.action == "SELL" and trade.take_profit >= trade.entry_price:
            return RiskDecision(
                approved=False,
                reason=(
                    "Trade rejected: SELL take-profit "
                    "must be below entry price."
                ),
                position_value=position_value,
                stop_loss=trade.stop_loss,
                take_profit=trade.take_profit
            )

        # --------------------------------------
        # 6. Maximum 2% capital allocation
        # --------------------------------------

        max_position_value = (
            portfolio.total_equity *
            self.max_capital_allocation
        )

        if position_value > max_position_value:
            return RiskDecision(
                approved=False,
                reason=(
                    f"Trade blocked: position value "
                    f"${position_value:.2f} exceeds the "
                    f"2% capital limit of "
                    f"${max_position_value:.2f}."
                ),
                position_value=position_value,
                stop_loss=trade.stop_loss,
                take_profit=trade.take_profit
            )

        # --------------------------------------
        # 7. Daily drawdown check
        # --------------------------------------

        daily_loss = (
            portfolio.starting_daily_equity -
            portfolio.total_equity
        )

        if daily_loss > 0:

            daily_drawdown = (
                daily_loss /
                portfolio.starting_daily_equity
            )

            if daily_drawdown >= self.daily_drawdown_limit:
                return RiskDecision(
                    approved=False,
                    reason=(
                        "Trade blocked: daily drawdown "
                        "limit of 3% has been reached."
                    ),
                    position_value=position_value,
                    stop_loss=trade.stop_loss,
                    take_profit=trade.take_profit
                )

        # --------------------------------------
        # 8. Calculate mandatory stop-loss
        # --------------------------------------

        if trade.action == "BUY":
            calculated_stop_loss = (
                trade.entry_price *
                (1 - self.stop_loss_percent)
            )

        else:  # SELL
            calculated_stop_loss = (
                trade.entry_price *
                (1 + self.stop_loss_percent)
            )

        # --------------------------------------
        # 9. Final approval
        # --------------------------------------

        return RiskDecision(
            approved=True,
            reason="Trade passed all risk management checks.",
            position_value=position_value,
            stop_loss=calculated_stop_loss,
            take_profit=trade.take_profit
        )