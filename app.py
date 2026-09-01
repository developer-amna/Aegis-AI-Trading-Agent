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

# -----------------------------------------------------------------------------
# CUSTOM EYE-CATCHING LUXURY & TECH STYLING (CSS)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Dark Theme Background */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* Gold Accent Headers */
    h1, h2, h3 {
        color: #D4AF37 !important;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* Custom Styling for Streamlit Metrics */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E222D 0%, #14171F 100%);
        border: 1px solid #D4AF37;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.15);
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0px 4px 20px rgba(212, 175, 55, 0.35);
        transform: translateY(-2px);
    }
    [data-testid="stMetricLabel"] {
        color: #A0AAB0 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    /* Customizing Table/Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 10px;
        overflow: hidden;
    }

    /* Customizing Download Button */
    .stDownloadButton button {
        background: linear-gradient(90deg, #D4AF37 0%, #AA7C11 100%) !important;
        color: #0E1117 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        box-shadow: 0px 0px 10px rgba(212, 175, 55, 0.3);
        transition: all 0.3s ease;
    }
    .stDownloadButton button:hover {
        box-shadow: 0px 0px 18px rgba(212, 175, 55, 0.7);
        transform: translateY(-2px);
    }

    /* Customizing Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #14171F;
        border-right: 1px solid rgba(212, 175, 55, 0.2);
    }
</style>
""", unsafe_allow_html=True)

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

# Charts Section
chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    st.subheader("📈 Portfolio Value Growth")
    time_series = pd.date_range(end=datetime.datetime.now(), periods=10, freq="1h")
    base_values = [100000, 100500, 101200, 100800, 102000, 102500, 103100, 104000, 104200, portfolio_val]
    growth_data = pd.DataFrame({
        "Time": time_series,
        "Portfolio Value ($)": base_values
    })
    fig_growth = px.line(growth_data, x="Time", y="Portfolio Value ($)", markers=True, template="plotly_dark")
    fig_growth.update_traces(line_color='#00FFA3')
    st.plotly_chart(fig_growth, use_container_width=True)

with chart_col2:
    st.subheader("📊 Asset Allocation")
    allocation_data = pd.DataFrame({
        "Asset": ["AAPL", "NVDA", "TSLA", "BTC", "Cash"],
        "Value ($)": [30000, 25000, 15000, 12750, cash_val]
    })
    fig_pie = px.pie(allocation_data, names="Asset", values="Value ($)", hole=0.4, template="plotly_dark")
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# Trade History & AI Agent Logs
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