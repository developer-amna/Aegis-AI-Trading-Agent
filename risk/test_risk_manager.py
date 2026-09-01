from risk_manager import RiskManager, TradeRequest, PortfolioState


def test_safe_trade():
    risk_manager = RiskManager()

    trade = TradeRequest(
        symbol="AAPL",
        action="BUY",
        entry_price=100,
        quantity=10,
        take_profit=105
    )

    portfolio = PortfolioState(
        total_equity=100000,
        starting_daily_equity=100000
    )

    result = risk_manager.validate_trade(trade, portfolio)

    print("\nSAFE BUY TEST")
    print(result)

    assert result.approved is True


def test_trade_over_2_percent():
    risk_manager = RiskManager()

    trade = TradeRequest(
        symbol="AAPL",
        action="BUY",
        entry_price=100,
        quantity=30,
        take_profit=105
    )

    portfolio = PortfolioState(
        total_equity=100000,
        starting_daily_equity=100000
    )

    result = risk_manager.validate_trade(trade, portfolio)

    print("\n2% CAPITAL LIMIT TEST")
    print(result)

    assert result.approved is False


def test_daily_drawdown_limit():
    risk_manager = RiskManager()

    trade = TradeRequest(
        symbol="AAPL",
        action="BUY",
        entry_price=100,
        quantity=10,
        take_profit=105
    )

    portfolio = PortfolioState(
        total_equity=97000,
        starting_daily_equity=100000
    )

    result = risk_manager.validate_trade(trade, portfolio)

    print("\nDAILY DRAWDOWN TEST")
    print(result)

    assert result.approved is False


def test_buy_with_invalid_stop_loss():
    risk_manager = RiskManager()

    trade = TradeRequest(
        symbol="AAPL",
        action="BUY",
        entry_price=100,
        quantity=10,
        stop_loss=101,
        take_profit=105
    )

    portfolio = PortfolioState(
        total_equity=100000,
        starting_daily_equity=100000
    )

    result = risk_manager.validate_trade(trade, portfolio)

    print("\nINVALID BUY STOP-LOSS TEST")
    print(result)

    assert result.approved is False


def test_buy_with_invalid_take_profit():
    risk_manager = RiskManager()

    trade = TradeRequest(
        symbol="AAPL",
        action="BUY",
        entry_price=100,
        quantity=10,
        stop_loss=98.5,
        take_profit=95
    )

    portfolio = PortfolioState(
        total_equity=100000,
        starting_daily_equity=100000
    )

    result = risk_manager.validate_trade(trade, portfolio)

    print("\nINVALID BUY TAKE-PROFIT TEST")
    print(result)

    assert result.approved is False


def test_safe_sell_trade():
    risk_manager = RiskManager()

    trade = TradeRequest(
        symbol="AAPL",
        action="SELL",
        entry_price=100,
        quantity=10,
        stop_loss=101.5,
        take_profit=95
    )

    portfolio = PortfolioState(
        total_equity=100000,
        starting_daily_equity=100000
    )

    result = risk_manager.validate_trade(trade, portfolio)

    print("\nSAFE SELL TEST")
    print(result)

    assert result.approved is True


def test_sell_with_invalid_stop_loss():
    risk_manager = RiskManager()

    trade = TradeRequest(
        symbol="AAPL",
        action="SELL",
        entry_price=100,
        quantity=10,
        stop_loss=99,
        take_profit=95
    )

    portfolio = PortfolioState(
        total_equity=100000,
        starting_daily_equity=100000
    )

    result = risk_manager.validate_trade(trade, portfolio)

    print("\nINVALID SELL STOP-LOSS TEST")
    print(result)

    assert result.approved is False


def test_sell_with_invalid_take_profit():
    risk_manager = RiskManager()

    trade = TradeRequest(
        symbol="AAPL",
        action="SELL",
        entry_price=100,
        quantity=10,
        stop_loss=101.5,
        take_profit=105
    )

    portfolio = PortfolioState(
        total_equity=100000,
        starting_daily_equity=100000
    )

    result = risk_manager.validate_trade(trade, portfolio)

    print("\nINVALID SELL TAKE-PROFIT TEST")
    print(result)

    assert result.approved is False


def test_invalid_action():
    risk_manager = RiskManager()

    trade = TradeRequest(
        symbol="AAPL",
        action="HOLD",
        entry_price=100,
        quantity=10,
        take_profit=105
    )

    portfolio = PortfolioState(
        total_equity=100000,
        starting_daily_equity=100000
    )

    result = risk_manager.validate_trade(trade, portfolio)

    print("\nINVALID ACTION TEST")
    print(result)

    assert result.approved is False