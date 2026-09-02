import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import random
import time

# Page Configuration
st.set_page_config(
    page_title="AI Trading Agent Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar Controls
st.sidebar.title("🛡️ AI Control Center")
st.sidebar.subheader("Filters & Controls")
timeframe = st.sidebar.selectbox("Select Timeframe", ["Live (1D)", "1 Week", "1 Month", "1 Year"])
risk_level = st.sidebar.slider("AI Risk Tolerance Threshold", 1, 10, 4)

auto_refresh = st.sidebar.checkbox("Enable Live Updates", value=False)
refresh_rate = st.sidebar.slider("Refresh Interval (Seconds)", 2, 10, 3)

st.sidebar.divider()
st.sidebar.success("✅ Risk Manager Agent Active")
st.sidebar.info("🤖 Unsafe Trade Protection: ON")

# Demo Control Button for Presentation
st.sidebar.subheader("🧪 Hackathon Demo Trigger")
trigger_unsafe_trade = st.sidebar.button("🚨 Simulate Unsafe Trade")

# Main Header
st.title("📈 AI Autonomous Trading Dashboard")
st.caption("Real-time portfolio tracking, trade execution history, and AI reasoning logs.")

st.divider()

# Live Simulated Values
portfolio_val = 104850 + random.randint(-200, 500)
cash_val = 22100 + random.randint(-100, 100)

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Total Portfolio Value", value=f"${portfolio_val:,.2f}", delta=f"{random.choice(['+', '-'])}${random.randint(10, 150)}.00")
col2.metric(label="Cash Balance", value=f"${cash_val:,.2f}")
col3.metric(label="Total Trades Today", value="16", delta="3 Unsafe Blocked")
col4.metric(label="Active AI Agents", value="3 Active")

st.divider()

# Demo Unsafe Trade Alert Banner
if trigger_unsafe_trade:
    st.error("🚨 **SECURITY ALERT:** High-frequency arbitrage bot attempted high-leverage trade (100x BTC). **ACTION: BLOCKED BY RISK-MANAGER AGENT**")

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
    st.subheader("📊 Recent Trade Execution History")
    trades_data = pd.DataFrame({
        "Timestamp": [
            datetime.datetime.now().strftime("%H:%M:%S"),
            (datetime.datetime.now() - datetime.timedelta(minutes=3)).strftime("%H:%M:%S"),
            (datetime.datetime.now() - datetime.timedelta(minutes=8)).strftime("%H:%M:%S"),
            (datetime.datetime.now() - datetime.timedelta(minutes=15)).strftime("%H:%M:%S")
        ],
        "Symbol": ["AAPL", "NVDA", "TSLA", "BTC/USD"],
        "Action": ["BUY", "SELL", "BUY", "BLOCK"],
        "Quantity": [10, 5, 12, 0.5],
        "Price ($)": [224.50, 128.30, 210.00, 64200.00],
        "Status": ["Executed", "Executed", "Executed", "🚫 Blocked (Unsafe)"]
    })
    st.dataframe(trades_data, use_container_width=True)
    
    # Download Button
    csv = trades_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Trade Execution Log (CSV)",
        data=csv,
        file_name="trade_execution_log.csv",
        mime="text/csv"
    )

with right_col:
    st.subheader("🤖 Live AI Agent Reasoning Logs")
    st.error("🛑 **Risk-Manager Agent:** Blocked high-risk BTC buy order due to high volatility.")
    st.success("🔵 **Trend-Follower Agent:** Executed BUY AAPL 10 shares based on MACD breakout.")
    st.warning("🟠 **Sentiment Agent:** Flagged news volatility spike for TSLA.")

# Auto-Refresh Loop Trigger
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()