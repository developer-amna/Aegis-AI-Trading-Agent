import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import random
import time
import itertools
from contextlib import contextmanager

from market_data import MarketDataCollector
from debate_engine import DebateEngine
from backtest_engine import Backtester

collector = MarketDataCollector()
engine = DebateEngine()
backtester = Backtester()

# ----------------------------------------------------------------------------
# Page Configuration
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="AEGIS-AI | Autonomous Trading System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------------------------
# Theme tokens
# ----------------------------------------------------------------------------
BG = "#0a0e1f"
CARD_BG = "#12172c"
CARD_BORDER = "rgba(139, 92, 246, 0.18)"
PURPLE = "#8b5cf6"
BLUE = "#3b82f6"
GREEN = "#00d68f"
RED = "#ef4444"
AMBER = "#f5a623"
TEXT_PRIMARY = "#e8eaf2"
TEXT_MUTED = "#8b91a8"

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG}; color: {TEXT_PRIMARY}; }}
    section[data-testid="stSidebar"] {{
        background-color: #0d1225;
        border-right: 1px solid {CARD_BORDER};
    }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    .brand {{ display:flex; align-items:center; gap:10px; padding: 4px 4px 18px 4px; }}
    .brand-icon {{
        width: 42px; height: 42px; border-radius: 12px;
        background: linear-gradient(135deg, {PURPLE}, {BLUE});
        display:flex; align-items:center; justify-content:center; font-size:20px;
    }}
    .brand-title {{ font-size: 18px; font-weight: 800; color: {TEXT_PRIMARY}; line-height:1.1; }}
    .brand-sub {{ font-size: 11px; color: {TEXT_MUTED}; }}

    .ai-status-card {{
        background: {CARD_BG}; border: 1px solid {CARD_BORDER};
        border-radius: 14px; padding: 14px; margin-top: 14px;
    }}
    .ai-status-title {{ font-size: 13px; font-weight: 600; color: {TEXT_PRIMARY}; }}
    .ai-status-dot {{ color: {GREEN}; font-size: 12px; }}

    .ticker-bar {{
        display: flex; align-items: center; gap: 32px;
        background: {CARD_BG}; border: 1px solid {CARD_BORDER};
        border-radius: 14px; padding: 14px 22px; margin-bottom: 20px;
    }}
    .ticker-item {{ font-size: 15px; color: {TEXT_PRIMARY}; white-space: nowrap; }}
    .ticker-item span.sym {{ color: {TEXT_MUTED}; margin-right: 6px; }}
    .ticker-up {{ color: {GREEN}; }}
    .ticker-down {{ color: {RED}; }}
    .status-pill {{
        margin-left: auto; background: rgba(0, 214, 143, 0.12); color: {GREEN};
        border: 1px solid rgba(0, 214, 143, 0.35); border-radius: 20px;
        padding: 5px 14px; font-size: 13px; font-weight: 600; white-space: nowrap;
    }}

    .metric-card {{
        background: {CARD_BG}; border: 1px solid {CARD_BORDER};
        border-radius: 16px; padding: 16px 18px; height: 100%;
    }}
    .metric-label {{ color: {TEXT_MUTED}; font-size: 12px; margin-bottom: 8px; }}
    .metric-value {{ color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 700; }}
    .metric-sub {{ font-size: 12px; margin-top: 5px; }}

    .panel-title {{ font-size: 14px; font-weight: 600; color: {TEXT_PRIMARY}; margin-bottom: 14px; }}

    .row-line {{
        display:flex; justify-content: space-between; align-items:center;
        padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px;
    }}
    .row-line:last-child {{ border-bottom: none; }}
    .row-label {{ color: {TEXT_MUTED}; }}
    .row-value {{ color: {TEXT_PRIMARY}; font-weight: 600; }}

    .decision-badge {{
        display: inline-block; padding: 6px 18px; border-radius: 8px;
        font-weight: 700; font-size: 14px;
    }}
    .badge-buy {{ background: rgba(0, 214, 143, 0.15); color: {GREEN}; }}
    .badge-sell {{ background: rgba(239, 68, 68, 0.15); color: {RED}; }}
    .badge-hold {{ background: rgba(139, 146, 168, 0.15); color: {TEXT_MUTED}; }}

    .news-bar {{
        background: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 14px;
        padding: 12px 20px; display:flex; align-items:center; gap: 24px;
        font-size: 13px; color: {TEXT_MUTED}; margin-top: 6px; flex-wrap: wrap;
    }}

    div[data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; }}

    /* --- Sidebar nav list (mirrors the reference dashboard) --- */
    section[data-testid="stSidebar"] div[role="radiogroup"] {{ gap: 3px; }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        display: flex; align-items: center; gap: 10px;
        padding: 10px 14px; border-radius: 12px;
        color: {TEXT_MUTED}; font-size: 14px; font-weight: 500;
        cursor: pointer; transition: background 0.15s ease; width: 100%;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        background: rgba(255,255,255,0.04);
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{
        display: none;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked),
    section[data-testid="stSidebar"] div[role="radiogroup"] label[aria-checked="true"] {{
        background: linear-gradient(90deg, {PURPLE}, {BLUE});
        color: #ffffff; font-weight: 700;
        box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35);
    }}

    /* --- Buttons (match dark theme instead of Streamlit's default white) --- */
    .stButton > button, .stDownloadButton > button {{
        background: linear-gradient(90deg, {PURPLE}, {BLUE});
        color: #ffffff; border: none; border-radius: 10px;
        font-weight: 600; padding: 0.55rem 1rem;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        filter: brightness(1.12); color: #ffffff;
    }}
    section[data-testid="stSidebar"] .stButton > button {{
        background: rgba(239, 68, 68, 0.15); color: {RED};
        border: 1px solid rgba(239, 68, 68, 0.35);
    }}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# panel(): draws a bordered container styled as a dark card, with a title.
# Uses a hidden marker span + CSS :has() so the title AND any native
# Streamlit widgets (charts, tables, buttons) placed inside render inside
# the SAME visual box, instead of Streamlit splitting raw HTML divs from
# native widgets into separate boxes.
# ----------------------------------------------------------------------------
_panel_seq = itertools.count()

@contextmanager
def panel(title: str):
    marker = f"pnl-{next(_panel_seq)}"
    box = st.container(border=True)
    with box:
        st.markdown(
            f'<span class="{marker}"></span><div class="panel-title">{title}</div>',
            unsafe_allow_html=True
        )
        yield
    st.markdown(f"""
    <style>
        div[data-testid="stVerticalBlockBorderWrapper"]:has(span.{marker}) {{
            background: {CARD_BG} !important;
            border: 1px solid {CARD_BORDER} !important;
            border-radius: 16px !important;
        }}
    </style>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
st.sidebar.markdown("""
<div class="brand">
    <div class="brand-icon">🛡️</div>
    <div>
        <div class="brand-title">AEGIS-AI</div>
        <div class="brand-sub">Autonomous Trading System</div>
    </div>
</div>
""", unsafe_allow_html=True)

NAV_ITEMS = [
    ("🏠", "Dashboard"), ("📈", "Market Overview"), ("💡", "AI Decisions"),
    ("💼", "Portfolio"), ("🧮", "Options Chain"), ("🛡️", "Risk Management"),
    ("🧾", "Trade History"), ("📊", "Performance"), ("📰", "News & Sentiment"),
    ("🗒️", "System Logs"), ("⚙️", "Settings"),
]
active_page = st.sidebar.radio("Navigate", [f"{i} {l}" for i, l in NAV_ITEMS],
                                index=0, label_visibility="collapsed")
active_label = active_page.split(" ", 1)[1]

with st.sidebar.expander("⚙️ Quick Controls", expanded=False):
    symbol = st.text_input("Stock Ticker", value="AAPL").upper()
    timeframe = st.selectbox("Timeframe", ["Live (1D)", "1 Week", "1 Month", "1 Year"])
    risk_level = st.slider("AI Risk Tolerance", 1, 10, 4)
    auto_refresh = st.checkbox("Enable Live Updates", value=False)
    refresh_rate = st.slider("Refresh Interval (s)", 2, 10, 3)
    trigger_unsafe_trade = st.button("🚨 Simulate Unsafe Trade", use_container_width=True)

st.sidebar.markdown(f"""
<div class="ai-status-card">
    <div class="ai-status-title">🧠 AI System Status</div>
    <div style="margin-top:8px;"><span class="ai-status-dot">●</span> All Systems Operational</div>
    <div style="color:{TEXT_MUTED}; font-size:12px; margin-top:4px;">
        Last Check: {datetime.datetime.now().strftime('%I:%M:%S %p')}
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Top ticker bar
# ----------------------------------------------------------------------------
now_str = datetime.datetime.now().strftime("%b %d, %Y  %I:%M:%S %p")
st.markdown(f"""
<div class="ticker-bar">
    <div class="ticker-item"><span class="sym">SPY</span>531.52 <span class="ticker-up">▲ 0.68%</span></div>
    <div class="ticker-item"><span class="sym">QQQ</span>452.81 <span class="ticker-up">▲ 0.72%</span></div>
    <div class="ticker-item"><span class="sym">VIX</span>14.35 <span class="ticker-down">▼ 1.65%</span></div>
    <div class="status-pill">● SYSTEM ONLINE</div>
    <div class="ticker-item" style="color:{TEXT_MUTED}; font-size:13px;">{now_str}</div>
</div>
""", unsafe_allow_html=True)

if active_label != "Dashboard":
    with panel(active_label):
        st.markdown(f"""
        <div style="text-align:center; padding: 50px 10px;">
            <div style="font-size:32px; margin-bottom:10px;">🚧</div>
            <div style="color:{TEXT_MUTED}; font-size:13px;">
                This section isn't wired up yet — Dashboard is the fully built page for the demo.
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ============================================================================
# DASHBOARD PAGE
# ============================================================================
st.markdown(f"<h2 style='margin-bottom:2px;'>🛡️ Aegis Autonomous AI Trading Dashboard</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{TEXT_MUTED}; margin-top:0;'>Real-time portfolio tracking, multi-agent debate reasoning, and trade execution.</p>", unsafe_allow_html=True)

if trigger_unsafe_trade:
    st.error("🚨 **SECURITY ALERT:** High-frequency arbitrage bot attempted a high-leverage trade (100x BTC). **ACTION: BLOCKED BY RISK-MANAGER AGENT**")

# ----------------------------------------------------------------------------
# Real backtested portfolio stats (Backtester runs the SAME rule logic as
# DebateEngine over historical prices — cached per symbol/timeframe so we
# don't re-run it on every Streamlit rerun/widget interaction).
# ----------------------------------------------------------------------------
TIMEFRAME_TO_PERIOD = {
    "Live (1D)": "3mo",
    "1 Week": "3mo",
    "1 Month": "6mo",
    "1 Year": "1y",
}
backtest_period = TIMEFRAME_TO_PERIOD.get(timeframe, "6mo")
cache_key = f"{symbol}_{backtest_period}"

if st.session_state.get("bt_cache_key") != cache_key:
    with st.spinner(f"Backtesting {symbol} over {backtest_period}..."):
        st.session_state["bt_result"] = backtester.run(symbol, period=backtest_period)
        st.session_state["bt_cache_key"] = cache_key

bt = st.session_state["bt_result"]
equity_curve = bt["equity_curve"]

portfolio_val = bt["ending_capital"]
if len(equity_curve) >= 2:
    todays_pnl = round(float(equity_curve.iloc[-1] - equity_curve.iloc[-2]), 2)
else:
    todays_pnl = 0.0
pnl_sign = "+" if todays_pnl >= 0 else ""
pnl_color = GREEN if todays_pnl >= 0 else RED

total_return_pct = bt["total_return_pct"]
total_return_abs = round(portfolio_val - bt["starting_capital"], 2)

win_count, total_trades = bt["win_count"], bt["total_trades"]
win_rate = bt["win_rate_pct"]

sharpe_ratio = bt["sharpe_ratio"]
max_drawdown = bt["max_drawdown_pct"]

# ----------------------------------------------------------------------------
# Row 1 — 5 key metric cards
# ----------------------------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">PORTFOLIO VALUE</div>
        <div class="metric-value">${portfolio_val:,.2f}</div>
        <div class="metric-sub" style="color:{pnl_color};">{pnl_sign}${abs(todays_pnl):,.2f} today</div>
    </div>""", unsafe_allow_html=True)

with c2:
    return_color = GREEN if total_return_abs >= 0 else RED
    return_sign = "+" if total_return_abs >= 0 else "-"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">TOTAL RETURN</div>
        <div class="metric-value">{total_return_pct}%</div>
        <div class="metric-sub" style="color:{return_color};">{return_sign}${abs(total_return_abs):,.2f} backtested</div>
    </div>""", unsafe_allow_html=True)

with c3:
    win_color = GREEN if win_rate >= 50 else (AMBER if win_rate >= 35 else RED)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">WIN RATE</div>
        <div class="metric-value">{win_rate}%</div>
        <div class="metric-sub" style="color:{win_color};">{win_count} / {total_trades} trades</div>
    </div>""", unsafe_allow_html=True)

with c4:
    sharpe_label = "Excellent" if sharpe_ratio >= 1.5 else ("Decent" if sharpe_ratio >= 0.5 else ("Weak" if sharpe_ratio >= 0 else "Negative"))
    sharpe_color = GREEN if sharpe_ratio >= 1.0 else (AMBER if sharpe_ratio >= 0 else RED)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">SHARPE RATIO</div>
        <div class="metric-value">{sharpe_ratio}</div>
        <div class="metric-sub" style="color:{sharpe_color};">{sharpe_label}</div>
    </div>""", unsafe_allow_html=True)

with c5:
    dd_label = "Well Controlled" if max_drawdown <= 10 else ("Moderate" if max_drawdown <= 20 else "High Risk")
    dd_color = GREEN if max_drawdown <= 10 else (AMBER if max_drawdown <= 20 else RED)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">MAX DRAWDOWN</div>
        <div class="metric-value">{max_drawdown}%</div>
        <div class="metric-sub" style="color:{dd_color};">{dd_label}</div>
    </div>""", unsafe_allow_html=True)

st.write("")

# ----------------------------------------------------------------------------
# Row 2 — Portfolio chart | Latest AI Decision | Sentiment donut
# ----------------------------------------------------------------------------
col_chart, col_decision, col_sentiment = st.columns([2, 1.2, 1])

with col_chart:
    with panel(f"📈 Portfolio Performance — {symbol} Backtest ({backtest_period})"):
        if len(equity_curve) > 0:
            growth_data = pd.DataFrame({"Time": equity_curve.index, "Value": equity_curve.values})
        else:
            # Empty backtest (e.g. brand-new/illiquid symbol) — flat line fallback
            growth_data = pd.DataFrame({
                "Time": pd.date_range(end=datetime.datetime.now(), periods=2, freq="D"),
                "Value": [portfolio_val, portfolio_val]
            })

        fig_growth = go.Figure()
        fig_growth.add_trace(go.Scatter(
            x=growth_data["Time"], y=growth_data["Value"],
            mode="lines", line=dict(color=PURPLE, width=3),
            fill="tozeroy", fillcolor="rgba(139, 92, 246, 0.10)",
        ))
        fig_growth.update_layout(
            template="plotly_dark", paper_bgcolor=CARD_BG, plot_bgcolor=CARD_BG,
            margin=dict(l=10, r=10, t=10, b=10), height=300,
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickprefix="$"),
        )
        st.plotly_chart(fig_growth, use_container_width=True, config={"displayModeBar": False})

with col_decision:
    with panel(f"💡 Latest AI Decision — {symbol}"):
        run_debate_btn = st.button("🚀 Run Live Agent Debate", use_container_width=True)
        result = st.session_state.get("last_decision")

        if run_debate_btn:
            with st.spinner(f"Running multi-agent consensus for {symbol}..."):
                payload = collector.fetch_stock_payload(symbol, risk_tolerance=risk_level)
                result = engine.run_debate(payload)
                st.session_state["last_decision"] = result

        if result:
            badge_class = {"BUY": "badge-buy", "SELL": "badge-sell", "HOLD": "badge-hold"}[result.action]
            st.markdown(f'<span class="decision-badge {badge_class}">{result.action}</span>', unsafe_allow_html=True)
            st.write("")
            st.markdown(f'<div class="row-line"><span class="row-label">Confidence</span><span class="row-value">{int(result.confidence*100)}%</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="row-line"><span class="row-label">Position Size</span><span class="row-value">{result.position_size_pct}%</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="row-line"><span class="row-label">Hedge Required</span><span class="row-value">{"Yes" if result.hedge_required else "No"}</span></div>', unsafe_allow_html=True)
            st.caption(result.reasoning)
            with st.expander("Bull / Bear case"):
                st.markdown(f"**🐂 Bull:** {result.bull_case}")
                st.markdown(f"**🐻 Bear:** {result.bear_case}")
        else:
            st.caption("Run the agent debate to see the latest AI decision here.")

with col_sentiment:
    with panel("📡 Sentiment Analysis"):
        pos, neu, neg = 82, 12, 6
        sentiment_score = round(pos / 100, 2)

        fig_sent = go.Figure(data=[go.Pie(
            labels=["Positive", "Neutral", "Negative"], values=[pos, neu, neg],
            hole=0.72, marker=dict(colors=[GREEN, AMBER, RED]), textinfo="none", sort=False,
        )])
        fig_sent.update_layout(
            template="plotly_dark", paper_bgcolor=CARD_BG, plot_bgcolor=CARD_BG,
            margin=dict(l=0, r=0, t=0, b=0), height=170, showlegend=False,
            annotations=[dict(text=f"<b>{sentiment_score}</b><br><span style='font-size:11px;color:{GREEN}'>BULLISH</span>",
                               x=0.5, y=0.5, font_size=18, showarrow=False, font_color=TEXT_PRIMARY)]
        )
        st.plotly_chart(fig_sent, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f'<div class="row-line"><span class="row-label">🟢 Positive</span><span class="row-value">{pos}%</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row-line"><span class="row-label">🟡 Neutral</span><span class="row-value">{neu}%</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="row-line"><span class="row-label">🔴 Negative</span><span class="row-value">{neg}%</span></div>', unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Row 3 — Market Overview | Asset Allocation | Performance Metrics | Open Positions
# ----------------------------------------------------------------------------
col_mkt, col_alloc, col_perf, col_pos = st.columns([1, 1, 1, 1.3])

with col_mkt:
    with panel("🌐 Market Overview"):
        market_rows = [
            ("S&P 500", "5,312.85", "+0.65%", True),
            ("NASDAQ 100", "18,302.11", "+0.92%", True),
            ("DOW JONES", "38,840.12", "+0.35%", True),
            ("VIX", "14.35", "-1.65%", False),
            ("10Y YIELD", "4.42%", "-0.28%", False),
        ]
        for name, val, chg, up in market_rows:
            color = GREEN if up else RED
            arrow = "▲" if up else "▼"
            st.markdown(f"""
            <div class="row-line">
                <span class="row-label">{name}</span>
                <span class="row-value">{val} <span style="color:{color};">{arrow} {chg}</span></span>
            </div>""", unsafe_allow_html=True)

with col_alloc:
    with panel("🥧 Asset Allocation"):
        alloc_labels = ["Equities", "Options", "Cash", "Others"]
        alloc_values = [60.2, 25.7, 10.1, 4.0]
        fig_alloc = go.Figure(data=[go.Pie(
            labels=alloc_labels, values=alloc_values, hole=0.65,
            marker=dict(colors=[BLUE, PURPLE, GREEN, AMBER]), textinfo="none",
        )])
        fig_alloc.update_layout(
            template="plotly_dark", paper_bgcolor=CARD_BG, plot_bgcolor=CARD_BG,
            margin=dict(l=0, r=0, t=0, b=0), height=150, showlegend=False,
            annotations=[dict(text=f"<b>${portfolio_val/1000:.1f}K</b><br><span style='font-size:10px;color:{TEXT_MUTED}'>Total Assets</span>",
                               x=0.5, y=0.5, font_size=14, showarrow=False, font_color=TEXT_PRIMARY)]
        )
        st.plotly_chart(fig_alloc, use_container_width=True, config={"displayModeBar": False})
        for label, val, color in zip(alloc_labels, alloc_values, [BLUE, PURPLE, GREEN, AMBER]):
            st.markdown(f'<div class="row-line"><span class="row-label">● {label}</span><span class="row-value">{val}%</span></div>', unsafe_allow_html=True)

with col_perf:
    with panel("📐 Performance Metrics"):
        perf_rows = [("Alpha", "1.85"), ("Beta", "0.92"), ("Sortino Ratio", "2.71"),
                     ("Calmar Ratio", "3.42"), ("Profit Factor", "2.35"), ("Expectancy", "$126.54")]
        for name, val in perf_rows:
            st.markdown(f'<div class="row-line"><span class="row-label">{name}</span><span class="row-value">{val}</span></div>', unsafe_allow_html=True)

with col_pos:
    with panel("📂 Open Positions"):
        positions_data = pd.DataFrame({
            "Symbol": [symbol, "MSFT", "SPY PUT", "TSLA", "QQQ PUT"],
            "Type": ["BUY", "BUY", "OPTION", "BUY", "OPTION"],
            "Size": [50, 30, 5, 20, 3],
            "P&L": [1125.00, 780.50, 645.25, -120.30, 210.75],
            "P&L %": ["+2.15%", "+1.85%", "+3.25%", "-0.45%", "+1.35%"],
        })
        st.dataframe(positions_data, use_container_width=True, hide_index=True, height=210)

# ----------------------------------------------------------------------------
# Trade history + AI agent logs
# ----------------------------------------------------------------------------
left_col, right_col = st.columns([2, 1])

with left_col:
    with panel("📊 Recent Trade Execution History"):
        trades_data = pd.DataFrame({
            "Timestamp": [
                datetime.datetime.now().strftime("%H:%M:%S"),
                (datetime.datetime.now() - datetime.timedelta(minutes=3)).strftime("%H:%M:%S"),
                (datetime.datetime.now() - datetime.timedelta(minutes=8)).strftime("%H:%M:%S"),
                (datetime.datetime.now() - datetime.timedelta(minutes=15)).strftime("%H:%M:%S")
            ],
            "Symbol": [symbol, "NVDA", "TSLA", "BTC/USD"],
            "Action": ["BUY", "SELL", "BUY", "BLOCK"],
            "Quantity": [10, 5, 12, 0.5],
            "Price ($)": [224.50, 128.30, 210.00, 64200.00],
            "Status": ["Executed", "Executed", "Executed", "🚫 Blocked (Unsafe)"]
        })
        st.dataframe(trades_data, use_container_width=True, hide_index=True)
        csv = trades_data.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Trade Execution Log (CSV)", data=csv,
                            file_name="trade_execution_log.csv", mime="text/csv")

with right_col:
    with panel("🤖 Live AI Agent Status Logs"):
        st.error("🛑 **Risk-Manager Agent:** Blocked high-risk BTC buy order due to high volatility.")
        st.success(f"🔵 **Trend-Follower Agent:** Executed BUY {symbol} 10 shares based on technical breakout.")
        st.warning("🟠 **Sentiment Agent:** Flagged news volatility spike for TSLA.")

# ----------------------------------------------------------------------------
# Bottom — AI News Feed
# ----------------------------------------------------------------------------
st.markdown(f"""
<div class="news-bar">
    <span style="color:{TEXT_PRIMARY}; font-weight:600;">📰 AI NEWS FEED</span>
    <span>Fed officials signal caution on rate cuts &nbsp;·&nbsp; 10:30 AM</span>
    <span>Apple unveils new AI features at WWDC &nbsp;·&nbsp; 09:45 AM</span>
    <span>Tech stocks rally on strong earnings &nbsp;·&nbsp; 09:15 AM</span>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Auto-refresh
# ----------------------------------------------------------------------------
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()