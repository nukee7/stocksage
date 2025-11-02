import streamlit as st

st.set_page_config(page_title="Chatbot | AI Financial Assistant", page_icon="🤖", layout="wide")

st.title("Chatbot Assistant")
st.markdown("Ask questions about markets, portfolios, and strategies.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I can help with markets, portfolios, and strategies. What would you like to know?"}
    ]

with st.sidebar:
    st.header("Chat Settings")
    persona = st.selectbox("Persona", ["General Advisor", "Risk-Aware", "Aggressive", "Educator"], index=0)
    style = st.selectbox("Answer Style", ["Concise", "Detailed"], index=0)
    st.divider()
    if st.button("New Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "New chat started. How can I help?"}
        ]
        st.rerun()

def respond(prompt: str, persona: str, style: str) -> str:
    prefix = {
        "General Advisor": "",
        "Risk-Aware": "[Risk-aware] ",
        "Aggressive": "[Aggressive] ",
        "Educator": "[Explain] ",
    }.get(persona, "")
    tone = "(concise)" if style == "Concise" else "(detailed)"
    return f"{prefix}{tone} I received: {prompt}. This is a placeholder response."

left_pad, chat_col, right_pad = st.columns([1, 2, 1])

with chat_col:
    top_bar = st.container()
    with top_bar:
        c1, c2 = st.columns([6, 1])
        with c1:
            st.caption("Chat session")
        with c2:
            if st.button("Clear", help="Clear conversation"):
                st.session_state.messages = []
                st.rerun()

    # Quick suggestions
    suggestions = [
        "What's today's market overview?",
        "Outlook for AAPL this week",
        "Build a 60/40 portfolio",
        "Explain P/E ratio simply",
    ]
    srow = st.container()
    with srow:
        sc1, sc2, sc3, sc4 = st.columns(4)
        for idx, col in enumerate([sc1, sc2, sc3, sc4]):
            with col:
                if st.button(suggestions[idx], use_container_width=True):
                    user_text = suggestions[idx]
                    st.session_state.messages.append({"role": "user", "content": user_text})
                    with st.chat_message("user", avatar="🧑"):
                        st.markdown(user_text)
                    with st.chat_message("assistant", avatar="🤖"):
                        with st.spinner("Thinking..."):
                            reply = respond(user_text, persona, style)
                            st.session_state.messages.append({"role": "assistant", "content": reply})
                            st.markdown(reply)
                    st.stop()

    chat = st.container()
    with chat:
        for msg in st.session_state.messages:
            avatar = "🤖" if msg["role"] == "assistant" else "🧑"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        user_input = st.chat_input("Type your message...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_input)

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    assistant_reply = respond(user_input, persona, style)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                    st.markdown(assistant_reply)
