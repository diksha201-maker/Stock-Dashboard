import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import date

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Market Analytics Hub",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
STOCKS = {
    "TRENT": {"name": "Trent Ltd", "base": 1200, "volatility": 0.022, "trend": 0.0012},
    "DMART": {"name": "Avenue Supermarket", "base": 3900, "volatility": 0.015, "trend": 0.0006},
    "REDTAPE": {"name": "Redtape Ltd", "base": 480, "volatility": 0.025, "trend": 0.0008},
    "SHOPSTOP": {"name": "Shoppers Stop", "base": 720, "volatility": 0.028, "trend": 0.0005},
    "ABFRL": {"name": "Aditya Birla Fashion", "base": 190, "volatility": 0.030, "trend": 0.0003},
}

# ✅ UPDATED FY
FY_RANGES = {
    "FY 2023-2024": (date(2023, 4, 1), date(2024, 3, 31)),
    "FY 2024-2025": (date(2024, 4, 1), date(2025, 3, 31)),
    "FY 2025-2026": (date(2025, 4, 1), date(2026, 3, 31)),  # Added
}

@st.cache_data
def generate_stock_data(ticker, start, end, seed=42):
    np.random.seed(seed + hash(ticker) % 100)
    dates = pd.bdate_range(start=start, end=end)
    n = len(dates)
    info = STOCKS[ticker]

    close = [info["base"]]
    for i in range(1, n):
        ret = info["trend"] + info["volatility"] * np.random.randn()
        close.append(close[-1] * (1 + ret))
    close = np.array(close)

    high = close * (1 + np.abs(np.random.normal(0, 0.008, n)))
    low  = close * (1 - np.abs(np.random.normal(0, 0.008, n)))
    open_ = low + (high - low) * np.random.uniform(0.2, 0.8, n)
    volume = np.random.randint(500000, 5000000, n)

    df = pd.DataFrame({
        "Date": dates, "Open": open_,
        "High": high, "Low": low,
        "Close": close, "Volume": volume
    })
    df["MA7"] = df["Close"].rolling(7).mean()
    df["MA30"] = df["Close"].rolling(30).mean()
    df["Daily_Return"] = df["Close"].pct_change() * 100
    return df

def get_all_data(fy):
    start, end = FY_RANGES[fy]
    return {t: generate_stock_data(t, start, end) for t in STOCKS}

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Controls")

    selected_fy = st.selectbox(
        "Financial Year",
        list(FY_RANGES.keys()),
        index=2  # Default latest FY
    )

    selected_ticker = st.selectbox("Stock", list(STOCKS.keys()))

    st.markdown("### Portfolio Weights")
    weights = {}
    for t in STOCKS:
        weights[t] = st.slider(t, 0, 100, 20)

# ─────────────────────────────────────────────
# WARNING (IMPORTANT)
# ─────────────────────────────────────────────
if selected_fy == "FY 2025-2026":
    st.warning("⚠️ FY 2025–26 data is simulated (forecast-based) for presentation.")

# ─────────────────────────────────────────────
# DATA LOAD
# ─────────────────────────────────────────────
all_data = get_all_data(selected_fy)

# ─────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────
st.title("📈 Stock Market Analytics Hub")

# ─────────────────────────────────────────────
# MARKET OVERVIEW
# ─────────────────────────────────────────────
st.subheader("Market Overview")

cols = st.columns(5)
for i, (ticker, df) in enumerate(all_data.items()):
    start = df["Close"].iloc[0]
    end = df["Close"].iloc[-1]
    change = (end - start) / start * 100
    cols[i].metric(ticker, f"₹{end:.0f}", f"{change:+.2f}%")

# ─────────────────────────────────────────────
# TREND CHART
# ─────────────────────────────────────────────
fig = go.Figure()
for t, df in all_data.items():
    norm = df["Close"] / df["Close"].iloc[0] * 100
    fig.add_trace(go.Scatter(x=df["Date"], y=norm, name=t))

fig.update_layout(template="plotly_dark", height=400)
st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# STOCK DEEP DIVE
# ─────────────────────────────────────────────
st.subheader("Stock Deep Dive")

df = all_data[selected_ticker]

fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True)

fig2.add_trace(go.Candlestick(
    x=df["Date"],
    open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"]
), row=1, col=1)

fig2.add_trace(go.Bar(
    x=df["Date"], y=df["Volume"]
), row=2, col=1)

fig2.update_layout(template="plotly_dark", height=500)
st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# PORTFOLIO
# ─────────────────────────────────────────────
st.subheader("Portfolio")

total_invested = 0
total_value = 0

for t, df in all_data.items():
    alloc = weights[t] / 100
    invest = 100000 * alloc
    units = invest / df["Close"].iloc[0]
    value = units * df["Close"].iloc[-1]

    total_invested += invest
    total_value += value

pnl = total_value - total_invested

st.metric("Total Invested", f"₹{total_invested:.0f}")
st.metric("Current Value", f"₹{total_value:.0f}", f"₹{pnl:+.0f}")

# ─────────────────────────────────────────────
# LIVE SIMULATION
# ─────────────────────────────────────────────
st.subheader("Live Simulation")

if st.button("Start Simulation"):
    prices = {t: all_data[t]["Close"].iloc[-1] for t in STOCKS}

    for _ in range(20):
        cols = st.columns(5)
        for i, t in enumerate(STOCKS):
            shock = np.random.randn() * 0.01
            prices[t] *= (1 + shock)
            cols[i].metric(t, f"₹{prices[t]:.0f}")
        time.sleep(1)

    st.success("Simulation Complete")