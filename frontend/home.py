import os
import streamlit as st

st.set_page_config(page_title="AI Financial Assistant", page_icon="💹", layout="wide")

logo_path = os.path.join("assets", "logo.png")
col_logo, col_title = st.columns([1, 5], vertical_alignment="center")
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
with col_title:
    st.title("AI Financial Assistant")
    st.markdown("Your Intelligent Portfolio, Prediction & Advisory Companion")

st.markdown("---")

left, right = st.columns(2)

with left:
    card = st.container(border=True)
    with card:
        try:
            st.page_link("pages/chatbot.py", label="🤖 Chatbot Assistant", icon=":material/smart_toy:")
        except Exception:
            if st.button("🤖 Chatbot Assistant", use_container_width=True):
                try:
                    st.switch_page("pages/chatbot.py")
                except Exception:
                    st.info("Use the sidebar to navigate to Chatbot.")
        st.markdown(
            "Talk to an AI financial advisor that answers queries and helps plan strategies."
        )

with right:
    card = st.container(border=True)
    with card:
        try:
            st.page_link("pages/portfolio.py", label="📊 Portfolio Dashboard", icon=":material/insights:")
        except Exception:
            if st.button("📊 Portfolio Dashboard", use_container_width=True):
                try:
                    st.switch_page("pages/portfolio.py")
                except Exception:
                    st.info("Use the sidebar to navigate to Portfolio.")
        st.markdown(
            "Explore stock analysis, predictions, and sentiment-based insights."
        )


st.markdown("---")

news = st.container(border=True)
with news:
    st.subheader("📰 Live Market News")
    st.markdown("Real-time headlines curated for your watchlist.")

    ctl1, ctl2, ctl3, ctl4 = st.columns([2, 2, 2, 2])
    with ctl1:
        category = st.selectbox(
            "Category",
            ["All", "Markets", "Stocks", "Crypto", "Economy", "Forex"],
            index=1,
        )
    with ctl2:
        tickers = st.text_input("Tickers", placeholder="AAPL, TSLA, NVDA")
    with ctl3:
        max_items = st.slider("Articles", min_value=5, max_value=30, value=10, step=5)
    with ctl4:
        refresh = st.selectbox("Refresh", ["Off", "15s", "30s", "60s", "5m"], index=0)

    st.divider()

    list_col = st.container()
    with list_col:
        for i in range(max_items):
            card = st.container(border=True)
            with card:
                st.markdown(f"**Headline {i+1}** · Source • 2m ago")
                st.markdown(
                    "Short summary placeholder. This will display a brief snippet of the article content."
                )
                meta1, meta2, meta3 = st.columns([1, 1, 2])
                with meta1:
                    st.markdown("Sentiment: Neutral")
                with meta2:
                    st.markdown("Ticker: —")
                with meta3:
                    st.link_button("Read", url="#")

