import streamlit as st
import requests
import time

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="Chatbot | AI Financial Assistant",
    page_icon="🤖",
    layout="wide"
)

API_URL = "http://localhost:8001/api/chat"  # your FastAPI chatbot endpoint

# -----------------------------
# HEADER
# -----------------------------
st.title("🤖 StockSage Chatbot Assistant")
st.markdown("Ask me anything about markets, portfolios, or financial strategies.")

# -----------------------------
# SIDEBAR SETTINGS
# -----------------------------
with st.sidebar:
    st.header("Chat Settings")
    persona = st.selectbox(
        "Persona",
        ["General Advisor", "Risk-Aware", "Aggressive", "Educator"],
        index=0
    )
    style = st.selectbox("Answer Style", ["Concise", "Detailed"], index=0)
    st.divider()
    if st.button("🆕 New Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "New chat started. How can I help you today?"}
        ]
        st.rerun()

# -----------------------------
# STATE INIT
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I can help with markets, portfolios, and strategies. What would you like to know?"}
    ]

# -----------------------------
# HELPER: BACKEND CALL
# -----------------------------
def get_chatbot_reply(prompt: str, persona: str, style: str):
    """Call FastAPI chatbot backend."""
    try:
        payload = {
            "query": f"[{persona}] [{style}] {prompt}"
        }
        response = requests.post(API_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "Sorry, I didn’t get that.")
        else:
            return f"⚠️ API Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"❌ Connection error: {e}"

# -----------------------------
# MAIN CHAT CONTAINER
# -----------------------------
left_pad, chat_col, right_pad = st.columns([1, 2, 1])

with chat_col:
    # Top bar
    with st.container():
        c1, c2 = st.columns([6, 1])
        with c1:
            st.caption("💬 Chat Session")
        with c2:
            if st.button("🧹 Clear", help="Clear conversation"):
                st.session_state.messages = []
                st.rerun()

    # Quick suggestions
    suggestions = [
        "What's today's market overview?",
        "Outlook for AAPL this week",
        "Build a 60/40 portfolio",
        "Explain P/E ratio simply",
    ]
    with st.container():
        cols = st.columns(4)
        for i, col in enumerate(cols):
            with col:
                if st.button(suggestions[i], use_container_width=True):
                    user_msg = suggestions[i]
                    st.session_state.messages.append({"role": "user", "content": user_msg})
                    with st.chat_message("user", avatar="🧑"):
                        st.markdown(user_msg)
                    with st.chat_message("assistant", avatar="🤖"):
                        with st.spinner("Thinking..."):
                            reply = get_chatbot_reply(user_msg, persona, style)
                            st.session_state.messages.append({"role": "assistant", "content": reply})
                            st.markdown(reply)
                    st.stop()

    # Display conversation
    for msg in st.session_state.messages:
        avatar = "🤖" if msg["role"] == "assistant" else "🧑"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Input box
    user_input = st.chat_input("Type your message...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                assistant_reply = get_chatbot_reply(user_input, persona, style)
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                st.markdown(assistant_reply)
