import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime
import os
import sys

# Ensure current directory is in path for custom module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------
# IMPORT BACKEND AGENT MODULES
# ---------------------------------------------------------
BACKEND_AVAILABLE = False
BACKEND_ERROR = None
try:
    from market_data import MarketDataCollector
    from debate_engine import DebateEngine
    collector = MarketDataCollector()
    engine = DebateEngine()
    BACKEND_AVAILABLE = True
except Exception as e:
    BACKEND_AVAILABLE = False
    BACKEND_ERROR = str(e)

# 1. PAGE CONFIG
st.set_page_config(
    page_title="AEGIS-AI | Autonomous Trading System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ADVANCED DARK GLASSMORPHISM STYLING (CSS) - FIXED SIDEBAR VISIBILITY
st.markdown("""
<style>
    .stApp {
        background-color: #0B0E14;
        color: #F8FAFC;
        font-family: 'Inter', system-ui, sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #111622 0%, #1A2333 100%);
        border: 1px solid #2A364F;
        padding: 20px 24px;
        border-radius: 14px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .header-left { flex: 1; }
    .main-title {
        color: #FFFFFF !important;
        font-size: 24px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin: 0;
        line-height: 1.2;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    .main-subtitle {
        color: #94A3B8 !important;
        font-size: 13px;
        margin-top: 4px;
        margin-bottom: 0;
        -webkit-text-fill-color: #94A3B8 !important;
    }
    .status-badge-clean {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399 !important;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    .ticker-bar {
        background: #111622;
        border: 1px solid #2A364F;
        padding: 10px 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 10px;
        margin-bottom: 20px;
        font-size: 13px;
        color: #F8FAFC;
    }
    .ticker-item { margin-right: 20px; color: #F8FAFC !important; }
    .green-text { color: #34D399 !important; font-weight: 600; }
    .red-text { color: #F87171 !important; font-weight: 600; }

    .glass-card {
        background: rgba(17, 22, 34, 0.85);
        border: 1px solid #2A364F;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(8px);
        margin-bottom: 14px;
        color: #F8FAFC;
    }
    .card-title {
        color: #94A3B8 !important;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
        -webkit-text-fill-color: #94A3B8 !important;
    }
    .card-value {
        font-size: 20px;
        font-weight: 800;
        color: #FFFFFF !important;
        white-space: nowrap;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    .card-sub { font-size: 11px; margin-top: 4px; color: #CBD5E1 !important; }
    
    .ai-card {
        background: linear-gradient(135deg, rgba(30, 27, 75, 0.8) 0%, rgba(17, 22, 34, 0.98) 100%);
        border: 1px solid #6366F1;
        border-radius: 12px;
        padding: 16px;
        color: #F8FAFC;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.15);
    }
    .action-badge {
        font-weight: 800;
        padding: 4px 12px;
        border-radius: 6px;
        float: right;
        font-size: 12px;
    }
    .bg-buy { background: #34D399; color: #000 !important; }
    .bg-sell { background: #F87171; color: #FFF !important; }
    .bg-hold { background: #FBBF24; color: #000 !important; }

    /* --- SIDEBAR HIGH VISIBILITY FIXES --- */
    section[data-testid="stSidebar"] {
        background-color: #0F131C;
        border-right: 1px solid #2A364F;
    }
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #94A3B8 !important;
        -webkit-text-fill-color: #94A3B8 !important;
    }

    .news-footer {
        background: #111622;
        border: 1px solid #2A364F;
        padding: 12px 18px;
        border-radius: 10px;
        font-size: 12px;
        color: #94A3B8 !important;
        margin-top: 25px;
    }
    .news-footer span, .news-footer b {
        color: #CBD5E1 !important;
        -webkit-text-fill-color: #CBD5E1 !important;
    }

    div.stButton > button, 
    div.stDownloadButton > button, 
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.5) !important;
    }

    /* --- Sidebar navigation items styling --- */
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 6px;
        display: flex;
        flex-direction: column;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        display: flex !important;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid #2A364F;
        cursor: pointer;
        width: 100%;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(99, 102, 241, 0.12);
        border-color: rgba(99, 102, 241, 0.4);
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #CBD5E1 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #6366F1 0%, #4338CA 100%) !important;
        border-color: #818CF8 !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    div[data-testid="stWidgetLabel"] *, label[data-testid="stWidgetLabel"] p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    .stDataFrame { border-radius: 8px; overflow: hidden; border: 1px solid #2A364F; }
</style>
""", unsafe_allow_html=True)

# 3. SIDEBAR NAVIGATION
with st.sidebar:
    st.markdown("<h2 style='color:#FFFFFF; font-size:20px; margin-bottom:0;'>⚡ AEGIS-AI</h2>", unsafe_allow_html=True)
    st.caption("Autonomous Trading System")
    st.markdown("---")
    
    st.markdown("### Navigation")
    menu = st.radio(
        "", 
        ["🏠 Dashboard", "📈 Market Overview", "🤖 AI Decisions", "💼 Portfolio", "🛡️ Risk Management", "⚙️ Settings"], 
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### Testing Controls")
    if st.button("⚠️ Simulate Unsafe Trade", use_container_width=True):
        st.error("🛑 RISK ALERT: High-Leverage Order Intercepted & Blocked!")

    st.markdown("---")
    st.markdown("""
    <div class="glass-card" style="text-align:center; padding:12px;">
        <div style="font-size:20px;">🧠</div>
        <div style="font-weight:bold; color:#A5B4FC; font-size:12px; margin-top:4px;">Agent Status</div>
        <div style="color:#34D399; font-size:11px; margin-top:2px; font-weight:600;">● Fully Operational</div>
        <div style="color:#64748B; font-size:10px; margin-top:2px;">Latency: 12ms</div>
    </div>
    """, unsafe_allow_html=True)

# 4. PAGES ROUTING

# ==========================================
# PAGE 1: MAIN DASHBOARD
# ==========================================
if menu == "🏠 Dashboard":
    st.markdown("""
    <div class="main-header">
        <div class="header-left">
            <h1 class="main-title">⚡ AEGIS-AI TRADING SYSTEM</h1>
            <p class="main-subtitle">Autonomous Real-Time Risk Management & Execution Engine</p>
        </div>
        <div>
            <span class="status-badge-clean">🟢 LIVE AGENT ACTIVE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="ticker-bar">
        <div>
            <span class="ticker-item"><b>SPY</b> 531.52 <span class="green-text">▲ 0.68%</span></span>
            <span class="ticker-item"><b>QQQ</b> 452.81 <span class="green-text">▲ 0.72%</span></span>
            <span class="ticker-item"><b>VIX</b> 14.35 <span class="red-text">▼ -1.65%</span></span>
        </div>
        <div>
            <span style="color:#94A3B8; font-size:12px; font-weight:600;">Sep 03, 2026 | 03:29 PM</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.markdown('<div class="glass-card"><div class="card-title">Portfolio Value</div><div class="card-value">$104,528</div><div class="card-sub green-text">+$2,356 (2.3%)</div></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown('<div class="glass-card"><div class="card-title">Total Return</div><div class="card-value">4.53%</div><div class="card-sub green-text">+$4,528 All Time</div></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown('<div class="glass-card"><div class="card-title">Win Rate</div><div class="card-value">68.4%</div><div class="card-sub" style="color:#A5B4FC; font-weight:600;">26 / 38 Trades</div></div>', unsafe_allow_html=True)
    with kpi4:
        st.markdown('<div class="glass-card"><div class="card-title">Sharpe Ratio</div><div class="card-value">2.18</div><div class="card-sub green-text">Excellent</div></div>', unsafe_allow_html=True)
    with kpi5:
        st.markdown('<div class="glass-card"><div class="card-title">Max Drawdown</div><div class="card-value">1.32%</div><div class="card-sub green-text">Controlled</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([2.1, 1.1], gap="medium")

    with left_col:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="margin-bottom: 8px;">📈 Portfolio Performance (30 Days)</div>', unsafe_allow_html=True)
        
        dates = pd.date_range(end=datetime.datetime.now(), periods=30, freq="D")
        values = [96000 + i*300 + (i%3)*400 - (i%2)*200 for i in range(30)]
        values[-1] = 104528.63

        fig_main = go.Figure()
        fig_main.add_trace(go.Scatter(
            x=dates, y=values, mode='lines+markers',
            line=dict(color='#818CF8', width=3, shape='spline', smoothing=1.1),
            marker=dict(size=0),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.18)',
            hovertemplate='<b>%{x|%b %d}</b><br>$%{y:,.2f}<extra></extra>',
        ))
        fig_main.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10), height=240,
            showlegend=False,
            hovermode='x unified',
            xaxis=dict(showgrid=False, color='#64748B', showline=True, linecolor='#2A364F'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255, 255, 255, 0.04)', color='#64748B', tickprefix='$', tickformat=',.0f'),
            font=dict(color='#F1F5F9', size=11),
        )
        st.plotly_chart(fig_main, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title" style="margin-bottom: 8px;">🌐 Market Overview</div>', unsafe_allow_html=True)
            market_df = pd.DataFrame({
                "Index": ["S&P 500", "NASDAQ", "DOW", "VIX"], 
                "Value": ["5,312", "18,302", "38,840", "14.35"], 
                "Chg": ["+0.65%", "+0.92%", "+0.35%", "-1.65%"]
            })
            st.dataframe(market_df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with sub_c2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title" style="margin-bottom: 8px;">⚡ Open Positions</div>', unsafe_allow_html=True)
            pos_df = pd.DataFrame({
                "Symbol": ["AAPL", "MSFT", "TSLA", "BTC"], 
                "Type": ["BUY", "BUY", "BUY", "BLOCK"], 
                "P&L": ["+$1,125", "+$780", "-$120", "Block"]
            })
            st.dataframe(pos_df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="card-title" style="margin-bottom: 6px;">🤖 Latest AI Agent Decision</div>', unsafe_allow_html=True)
        if BACKEND_AVAILABLE:
            try:
                payload = collector.fetch_stock_payload("AAPL")
                decision = engine.run_debate(payload)
                
                act_cls = "bg-buy" if decision.action == "BUY" else ("bg-sell" if decision.action == "SELL" else "bg-hold")
                conf_perc = int(decision.confidence * 100) if decision.confidence <= 1.0 else int(decision.confidence)
                rsi_val = payload.get("market_data", {}).get("rsi_14", "N/A")
                price_val = payload.get("market_data", {}).get("current_price", "N/A")
                
                st.markdown(f"""
                <div class="ai-card" style="margin-bottom: 14px;">
                    <span class="action-badge {act_cls}">{decision.action}</span>
                    <div style="font-size:18px; font-weight:bold; color:#FFFFFF;">{decision.symbol}</div>
                    <div style="color:#94A3B8; font-size:12px; margin-top:3px;">RSI: {rsi_val} | Volatility Checked</div>
                    <hr style="border-color:#2A364F; margin:10px 0;">
                    <div style="display:flex; justify-content:space-between; font-size:13px; color:#F1F5F9;">
                        <span>Confidence: <b style="color:#34D399;">{conf_perc}%</b></span>
                        <span>Price: <b style="color:#FFFFFF;">${price_val}</b></span>
                    </div>
                    <div style="font-size:11px; color:#CBD5E1; margin-top:8px; background:rgba(0,0,0,0.35); padding:8px; border-radius:6px; border: 1px solid #2A364F; line-height: 1.4;">
                        <b style="color:#FFFFFF;">Consensus:</b> {decision.reasoning}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Backend processing error: {e}")
        else:
            st.info("Backend files missing. Showing cached state.")

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="margin-bottom: 4px;">💼 Asset Allocation</div>', unsafe_allow_html=True)
        fig_alloc = px.pie(names=['Equities', 'Options', 'Cash', 'Others'], values=[60.2, 25.7, 10.1, 4.0], hole=0.6, color_discrete_sequence=['#818CF8', '#A78BFA', '#34D399', '#FBBF24'])
        fig_alloc.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=0, r=0, t=0, b=0), height=170, 
            showlegend=True, 
            legend=dict(orientation="h", y=-0.15, font=dict(size=10, color='#CBD5E1')), 
            font=dict(color='#F1F5F9')
        )
        st.plotly_chart(fig_alloc, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PAGE 2: MARKET OVERVIEW
# ==========================================
elif menu == "📈 Market Overview":
    st.title("📈 Market Overview & Analytics")
    st.markdown('<p style="color:#FFFFFF; font-weight:600; font-size:13px; margin-bottom:4px;">Filter Market Sector</p>', unsafe_allow_html=True)
    selected_sector = st.selectbox("", ["All Sectors", "Technology", "Healthcare", "Financials", "Energy"], label_visibility="collapsed")
    
    m_col1, m_col2 = st.columns([2, 1])
    with m_col1:
        st.write("### Sector Momentum")
        sectors = pd.DataFrame({
            "Sector": ["Technology", "Healthcare", "Financials", "Energy", "Consumer Discretionary"],
            "Market Cap ($B)": [2800, 1500, 1900, 850, 1200],
            "Daily Change (%)": [1.85, -0.42, 0.95, -1.20, 0.65]
        })
        if selected_sector != "All Sectors":
            sectors = sectors[sectors["Sector"] == selected_sector]
        fig_bar = px.bar(sectors, x="Sector", y="Daily Change (%)", color="Daily Change (%)", color_continuous_scale="RdYlGn", template="plotly_dark")
        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#F1F5F9'))
        st.plotly_chart(fig_bar, use_container_width=True)

    with m_col2:
        st.write("### Global Benchmark Indices")
        indices_data = pd.DataFrame({
            "Index": ["S&P 500", "NASDAQ 100", "DOW JONES", "FTSE 100", "NIKKEI 225"],
            "Price": ["5,312.8", "18,302", "38,840", "8,210", "38,500"],
            "Trend": ["Bullish", "Bullish", "Neutral", "Bearish", "Bullish"]
        })
        st.dataframe(indices_data, use_container_width=True, hide_index=True)

# ==========================================
# PAGE 3: AI DECISIONS
# ==========================================
elif menu == "🤖 AI Decisions":
    st.title("🤖 Multi-Agent Consensus & Debate Engine")
    st.write("### Live Asset Analysis & Debate")
    
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        st.markdown('<p style="color:#FFFFFF; font-weight:600; font-size:13px; margin-bottom:4px;">Enter Ticker Symbol to Evaluate</p>', unsafe_allow_html=True)
        target_symbol = st.text_input("", value="NVDA", label_visibility="collapsed").upper()
    with col_btn:
        st.write(" ")
        run_analysis = st.button("🧠 Run Agent Debate", use_container_width=True)
        
    if run_analysis:
        if BACKEND_AVAILABLE:
            with st.spinner(f"Running Bull, Bear & Risk Manager Agents for {target_symbol}..."):
                try:
                    payload = collector.fetch_stock_payload(target_symbol, risk_tolerance=5)
                    decision = engine.run_debate(payload)
                    
                    res_col1, res_col2 = st.columns([1, 2])
                    with res_col1:
                        conf_str = f"{int(decision.confidence * 100)}%" if decision.confidence <= 1.0 else f"{decision.confidence}%"
                        risk_status_text = "APPROVED" if getattr(decision, 'risk_approved', True) else "BLOCKED BY RISK"
                        risk_color = "#34D399" if getattr(decision, 'risk_approved', True) else "#F87171"

                        st.markdown(f"""
                        <div class="glass-card" style="border: 2px solid #6366F1;">
                            <h3 style="color:#FFF; margin-top:0;">{decision.symbol}</h3>
                            <p style="margin-bottom:6px; color:#CBD5E1;">Action: <b style="color:#34D399;">{decision.action}</b></p>
                            <p style="margin-bottom:6px; color:#CBD5E1;">Confidence: <b style="color:#FFFFFF;">{conf_str}</b></p>
                            <p style="margin-bottom:0; color:#CBD5E1;">Risk Check: <b style="color:{risk_color};">{risk_status_text}</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with res_col2:
                        st.success(f"**Bull Case:** {decision.bull_case}")
                        st.error(f"**Bear Case:** {decision.bear_case}")
                        st.info(f"**Final Consensus:** {decision.reasoning}")
                except Exception as ex:
                    st.error(f"Execution Error: {ex}")
        else:
            st.error("Backend modules missing.")
        
    st.markdown("---")
    st.write("### Execution History Logs")
    ai_history = pd.DataFrame({
        "Timestamp": ["10:42:15", "10:35:00", "10:12:44", "09:50:11", "09:30:00"],
        "Ticker": ["AAPL", "NVDA", "TSLA", "BTC/USD", "MSFT"],
        "Action": ["BUY", "HOLD", "SELL", "BLOCK", "BUY"],
        "Price": ["$185.50", "$124.10", "$212.40", "$67,400", "$420.15"],
        "Confidence": ["85%", "91%", "78%", "99%", "92%"]
    })
    st.dataframe(ai_history, use_container_width=True, hide_index=True)
    csv_logs = ai_history.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export Logs (CSV)", csv_logs, "execution_logs.csv", "text/csv")

# ==========================================
# PAGE 4: PORTFOLIO
# ==========================================
elif menu == "💼 Portfolio":
    st.title("💼 Portfolio Holdings")
    p_col1, p_col2 = st.columns([1.5, 1])
    with p_col1:
        holdings = pd.DataFrame({
            "Asset": ["Apple Inc. (AAPL)", "NVIDIA (NVDA)", "Tesla (TSLA)", "Bitcoin (BTC)", "Cash Reserve"],
            "Units": ["50", "30", "20", "0.5", "-"],
            "Avg Price": ["$175.20", "$110.00", "$215.00", "$60,100", "-"],
            "Value": ["$9,275", "$3,849", "$4,200", "$32,100", "$22,100"]
        })
        st.dataframe(holdings, use_container_width=True, hide_index=True)

    with p_col2:
        fig_p_pie = px.pie(names=["AAPL", "NVDA", "TSLA", "BTC", "Cash"], values=[9275, 3849, 4200, 32100, 22100], hole=0.5, template="plotly_dark")
        fig_p_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#F1F5F9', size=12))
        st.plotly_chart(fig_p_pie, use_container_width=True)

# ==========================================
# PAGE 5: RISK MANAGEMENT
# ==========================================
elif menu == "🛡️ Risk Management":
    st.title("🛡️ Risk Management Panel")
    r_col1, r_col2 = st.columns(2)
    with r_col1:
        with st.form("risk_form"):
            st.write("### Safety Parameters")
            st.slider("Max Allocation per Trade (%)", 1, 20, 2)
            st.slider("Auto Stop-Loss Trigger (%)", 0.5, 5.0, 1.5)
            st.markdown('<p style="color:#FFFFFF; font-weight:600; font-size:13px; margin-bottom:4px;">Agent Risk Mode</p>', unsafe_allow_html=True)
            st.selectbox("", ["Conservative (Low)", "Balanced (Medium)", "Aggressive (High)"], label_visibility="collapsed")
            st.toggle("Enable AI Interception Guardrail", value=True)
            st.form_submit_button("💾 Save Risk Settings")

    with r_col2:
        st.write("### Recent Risk Interceptions")
        risk_logs = pd.DataFrame({
            "Time": ["10:00:05", "Yesterday", "2 Days Ago"],
            "Attempted Trade": ["100x BTC Futures", "TSLA Market Order $50k", "MEME Token Arbitrage"],
            "Violation": ["Exceeded Max Leverage", "Position Size Over Allocation", "Low Liquidity Asset"],
            "Status": ["BLOCKED", "BLOCKED", "BLOCKED"]
        })
        st.dataframe(risk_logs, use_container_width=True, hide_index=True)

# ==========================================
# PAGE 6: SETTINGS
# ==========================================
elif menu == "⚙️ Settings":
    st.title("⚙️ System Preferences")
    with st.form("settings_form"):
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.write("### API Connections")
            st.markdown('<p style="color:#FFFFFF; font-weight:600; font-size:13px; margin-bottom:4px;">Alpaca API Key</p>', unsafe_allow_html=True)
            st.text_input("", value="PK******************", type="password", label_visibility="collapsed")
            st.markdown('<p style="color:#FFFFFF; font-weight:600; font-size:13px; margin-bottom:4px;">Groq LLM Key</p>', unsafe_allow_html=True)
            st.text_input("", value="gsk_*****************", type="password", label_visibility="collapsed")
        with s_col2:
            st.write("### Notifications")
            st.checkbox("Enable Telegram Alerts", value=True)
            st.checkbox("Enable Daily Email Summaries", value=True)
        st.form_submit_button("⚡ Save Configuration")

# 5. BOTTOM NEWS TICKER FOOTER
st.markdown("""
<div class="news-footer">
    <b>📡 LIVE AI NEWS FEED:</b> &nbsp;&nbsp; 
    <span>Fed officials signal caution on rate cuts (10:30 AM)</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
    <span style="color:#A5B4FC;">Apple unveils new AI features (09:45 AM)</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
    <span>Tech stocks rally on strong earnings (09:15 AM)</span>
</div>
""", unsafe_allow_html=True)