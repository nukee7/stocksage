# pages/home.py
import os
from datetime import datetime, timedelta
import streamlit as st

st.set_page_config(page_title="AI Financial Assistant", page_icon="💹", layout="wide")

# --- Header ---
logo_path = os.path.join("assets", "logo.png")
col_logo, col_title = st.columns([1, 6], vertical_alignment="center")
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
with col_title:
    st.title("AI Financial Assistant")
    st.markdown("Your Intelligent Portfolio, Prediction & Advisory Companion")

st.markdown("---")

# --- Left / Right navigation cards ---
left, right = st.columns(2)
with left:
    card = st.container()
    with card:
        try:
            # For newer Streamlit you can use page_link; fallback to button
            st.page_link("pages/chatbot.py", label="🤖 Chatbot Assistant", icon=":material/smart_toy:")
        except Exception:
            if st.button("🤖 Chatbot Assistant", use_container_width=True):
                st.info("Open Chatbot from the sidebar (or use the app navigation).")
        st.markdown(
            "Talk to an AI financial advisor that answers queries and helps plan strategies."
        )

with right:
    card = st.container()
    with card:
        try:
            st.page_link("pages/portfolio.py", label="📊 Portfolio Dashboard", icon=":material/insights:")
        except Exception:
            if st.button("📊 Portfolio Dashboard", use_container_width=True):
                st.info("Open Portfolio from the sidebar (or use the app navigation).")
        st.markdown(
            "Explore stock analysis, predictions, and sentiment-based insights."
        )

st.markdown("---")

# ------------------------
# HARDCODED NEWS (with sentiment)
# ------------------------
HARDCODED_NEWS = [
    {
        "title": "Apple reports mixed revenue as iPhone demand cools",
        "source": "Reuters",
        "time": datetime.utcnow() - timedelta(hours=1, minutes=12),
        "summary": "Apple reported quarterly revenue that slightly missed expectations as iPhone sales slowed in key regions.",
        "tickers": ["AAPL"],
        "category": "Stocks",
        "sentiment": "negative",
        "url": "https://www.reuters.com/technology/apple-reports-q3-2025-results"
    },
    {
        "title": "Tesla announces new battery plant in Texas",
        "source": "Bloomberg",
        "time": datetime.utcnow() - timedelta(hours=3, minutes=5),
        "summary": "Tesla unveiled a new battery manufacturing facility aimed at boosting domestic production and lowering costs.",
        "tickers": ["TSLA"],
        "category": "Markets",
        "sentiment": "positive",
        "url": "https://www.bloomberg.com/tesla-battery-plant-texas"
    },
    {
        "title": "NVIDIA beats earnings estimates with strong data center demand",
        "source": "CNBC",
        "time": datetime.utcnow() - timedelta(days=1, hours=2),
        "summary": "NVIDIA exceeded expectations due to exceptional AI GPU demand in data center markets.",
        "tickers": ["NVDA"],
        "category": "Stocks",
        "sentiment": "positive",
        "url": "https://www.cnbc.com/nvidia-earnings-2025"
    },
    {
        "title": "Federal Reserve leaves rates unchanged",
        "source": "AP",
        "time": datetime.utcnow() - timedelta(hours=6),
        "summary": "The Fed held interest rates steady today amid mixed inflation and labor data.",
        "tickers": [],
        "category": "Economy",
        "sentiment": "neutral",
        "url": "https://apnews.com/fed-rate-decision-2025"
    },
    {
        "title": "Bitcoin dips below $40k amid profit-taking",
        "source": "CoinDesk",
        "time": datetime.utcnow() - timedelta(minutes=45),
        "summary": "Bitcoin dropped below the $40,000 mark after sustained investor profit-taking.",
        "tickers": ["BTC"],
        "category": "Crypto",
        "sentiment": "negative",
        "url": "https://www.coindesk.com/markets/bitcoin-dips-40k"
    },
    {
        "title": "Apple launches new AI tools to accelerate on-device machine learning",
        "source": "The Verge",
        "time": datetime.utcnow() - timedelta(hours=12),
        "summary": "Apple released new developer tools aimed at dramatically boosting on-device AI performance.",
        "tickers": ["AAPL"],
        "category": "Tech",
        "sentiment": "positive",
        "url": "https://www.theverge.com/apple-ai-developer-tools"
    },
]

# Sorting news by time (newest first)
HARDCODED_NEWS = sorted(HARDCODED_NEWS, key=lambda x: x["time"], reverse=True)

# ------------------------
# Controls
# ------------------------
st.subheader("📰 Live Market News")
st.markdown("Real-time headlines. Use the controls to filter and preview articles.")

ctl1, ctl2, ctl3, ctl4 = st.columns([2, 3, 2, 2])
with ctl1:
    category_filter = st.selectbox("Category", ["All", "Markets", "Stocks", "Crypto", "Economy", "Tech"], index=1)
with ctl2:
    tickers_input = st.text_input("Tickers (comma-separated)", placeholder="AAPL, TSLA, NVDA")
with ctl3:
    max_items = st.slider("Articles", min_value=3, max_value=12, value=6, step=1)
with ctl4:
    refresh = st.selectbox("Refresh", ["Off", "15s", "30s", "60s", "5m"], index=0)

st.divider()

# Helper to format time nicely (relative)
def time_ago(dt: datetime) -> str:
    diff = datetime.utcnow() - dt
    if diff.total_seconds() < 60:
        return f"{int(diff.total_seconds())}s ago"
    if diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() // 60)}m ago"
    if diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() // 3600)}h ago"
    return dt.strftime("%Y-%m-%d %H:%M UTC")

# Helper icon for sentiment
SENTIMENT_ICON = {
    "positive": "🟢",
    "negative": "🔴",
    "neutral": "🟡"
}

# Apply filters
filtered = []
ticker_terms = [t.strip().upper() for t in tickers_input.split(",") if t.strip()] if tickers_input else []
for article in HARDCODED_NEWS:
    if category_filter != "All" and article["category"] != category_filter:
        continue
    if ticker_terms:
        # include if any requested ticker is in article tickers (or ticker present in title)
        has = False
        for tk in ticker_terms:
            if tk in [s.upper() for s in article.get("tickers", [])]:
                has = True
                break
            if tk in article["title"].upper() or tk in article["summary"].upper():
                has = True
                break
        if not has:
            continue
    filtered.append(article)

# Limit to max items
filtered = filtered[:max_items]

# ------------------------
# Render news list
# ------------------------
for idx, article in enumerate(filtered):
    with st.container():
        # Main row: Title + meta + read button
        title_col, meta_col = st.columns([5, 1])
        with title_col:
            st.markdown(f"**{article['title']}**  ·  _{article['source']}_  ·  {time_ago(article['time'])}")
            st.write(article["summary"])
            # show tickers
            tickers = article.get("tickers", [])
            if tickers:
                st.markdown("**Tickers:** " + ", ".join(tickers))
            else:
                st.markdown("**Tickers:** —")
        with meta_col:
            sentiment = article.get("sentiment", "neutral")
            icon = SENTIMENT_ICON.get(sentiment, "⚪")
            st.markdown(f"**Sentiment**\n\n{icon} {sentiment.capitalize()}")
            # Read button
            if st.button("Read", key=f"read_{idx}", use_container_width=True):
                st.experimental_set_query_params(open=idx)
                st.markdown(f"[Open article]({article['url']})")

    st.markdown("---")

# --- Footer: small note ---
st.caption("This news feed is currently hardcoded for demo purposes. Replace HARDCODED_NEWS with your API call when ready.")