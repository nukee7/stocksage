# <-- PLACE THESE LINES AS THE VERY FIRST LINES IN frontend/pages/chatbot.py -->
import sys
from pathlib import Path

# If this file lives at <repo_root>/frontend/pages/chatbot.py,
# parents[2] walks up to the repo root (<repo_root>).
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))
# <-- end snippet -->
# pages/chatbot_test.py
import json
import logging
import traceback
import io
from typing import Any, Optional
import streamlit as st

# Try to import agent & creator (agent may fail to import at module load time)
try:
    from backend.langchain_core.utils.agent_builder import agent as agent_builder_agent
    from backend.langchain_core.utils.agent_builder import create_agent
except Exception:
    agent_builder_agent = None
    try:
        from backend.langchain_core.utils.agent_builder import create_agent  # type: ignore
    except Exception:
        create_agent = None  # type: ignore

from backend.langchain_core.utils.tools_config import tools

# ------------------------
# Streamlit UI Setup
# ------------------------
st.set_page_config(page_title="Agent Test — StockNews", layout="wide")
st.title("CHATBOT ")
st.markdown(
    "Answer related to stocks and portfolio using an AI agent with tools."
)

# input prompt
prompt = st.text_input("Write the query", value="Show me the latest news for AAPL")

col1, col2 = st.columns([3, 1])
with col2:
    run_btn = st.button("Go", type="primary")

# logging capture (StringIO)
log_stream = io.StringIO()
handler = logging.StreamHandler(log_stream)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# to avoid duplicate handlers in dev reloads, clear prior handlers
if len(root_logger.handlers) > 0:
    root_logger.handlers = []
root_logger.addHandler(handler)

logger = logging.getLogger("chatbot_test")

# ------------------------
# Helper functions (copied/adapted from your harness)
# ------------------------
def find_tool(name: str):
    for t in tools:
        if getattr(t, "name", None) == name:
            return t
    return None

def extract_symbol_simple(prompt_text: str) -> Optional[str]:
    for token in prompt_text.replace(",", " ").split():
        tok = token.strip().upper()
        if tok.isalpha() and 1 <= len(tok) <= 5:
            if tok in {"SHOW", "ME", "THE", "LATEST", "NEWS", "FOR", "PLEASE"}:
                continue
            return tok
    return None

def try_print_agent_prompt(agent_obj: Any):
    try:
        inner = getattr(agent_obj, "inner", agent_obj)
        prompt = None
        if hasattr(inner, "agent") and hasattr(inner.agent, "llm_chain"):
            prompt = getattr(inner.agent.llm_chain, "prompt", None)
        if prompt is None and hasattr(inner, "llm_chain"):
            prompt = getattr(inner.llm_chain, "prompt", None)
        if prompt is not None:
            tmpl = getattr(prompt, "template", None)
            if tmpl:
                logger.info("Agent prompt template (truncated): %s", (tmpl[:1000] + "...") if len(tmpl) > 1000 else tmpl)
            else:
                logger.info("Agent prompt object found but has no .template attribute.")
        else:
            logger.info("Could not find agent prompt object on agent (different langchain internals).")
    except Exception:
        logger.exception("Error while trying to read agent prompt template.")

def safe_agent_run(agent_obj: Any, prompt_text: str) -> str:
    attempts = []
    # 1) agent.run(prompt_text)
    try:
        if hasattr(agent_obj, "run"):
            logger.info("Attempting agent.run(prompt)...")
            out = agent_obj.run(prompt_text)
            logger.info("agent.run(prompt) succeeded.")
            return str(out)
    except Exception as e:
        attempts.append(("agent.run(prompt)", e))
        logger.warning("agent.run(prompt) failed: %s", e)

    # 2) agent(prompt_text) callable
    try:
        logger.info("Attempting agent(prompt) callable...")
        out = agent_obj(prompt_text)
        logger.info("agent(prompt) callable succeeded.")
        return str(out)
    except Exception as e:
        attempts.append(("agent(prompt)", e))
        logger.warning("agent(prompt) failed: %s", e)

    # 3) agent({'input': prompt_text})
    try:
        logger.info("Attempting agent({'input': prompt}) ...")
        out = agent_obj({"input": prompt_text})
        logger.info("agent({'input': prompt}) succeeded.")
        return str(out)
    except Exception as e:
        attempts.append(("agent({'input': prompt})", e))
        logger.warning("agent({'input': prompt}) failed: %s", e)

    # 4) agent.__call__({'input': prompt_text})
    try:
        logger.info("Attempting agent.__call__({'input': prompt}) ...")
        out = agent_obj.__call__({"input": prompt_text})
        logger.info("agent.__call__ succeeded.")
        return str(out)
    except Exception as e:
        attempts.append(("agent.__call__", e))
        logger.warning("agent.__call__ failed: %s", e)

    last_name, last_exc = attempts[-1]
    logger.error("All agent invocation attempts failed. Attempts: %s", [n for n, _ in attempts])
    raise last_exc

def direct_tool_test_section():
    logger.info("=== DIRECT TOOL TEST ===")
    tool = find_tool("StockNewsTool")
    if tool is None:
        logger.error("StockNewsTool not found in configured tools.")
        return {"error": "StockNewsTool not found."}

    results = {}
    test_inputs = [
        {"symbol": "AAPL"},
        '"AAPL"',  # JSON string representation
        "AAPL",    # plain string
    ]
    for i, inp in enumerate(test_inputs, start=1):
        try:
            logger.info("Direct call #%d with input: %s", i, inp)
            out = tool.func(inp)
            results[f"input_{i}"] = str(out)[:2000]
            logger.info("Direct call #%d succeeded (len=%d)", i, len(str(out)))
        except Exception:
            logger.exception("Direct tool call #%d failed.", i)
            results[f"input_{i}"] = f"CALL FAILED: see logs"
    return results

# ------------------------
# Main run logic (triggered by button)
# ------------------------
if run_btn:
    st.info("Running tests — check logs and outputs below.")
    logger.info("Device set to use mps:0")
    logger.info("INFO:backend.model.portfolio_model:Portfolio initialized with $100,000.00")

    # show configured tools
    try:
        tool_names = [t.name for t in tools]
    except Exception:
        tool_names = [getattr(t, "name", str(t)) for t in tools]
    logger.info("Configured tools: %s", tool_names)

    # Direct tool test
    direct_results = direct_tool_test_section()

    # Ensure agent exists (lazy creation if earlier import failed)
    agent_obj = agent_builder_agent
    if agent_obj is None:
        if create_agent is None:
            logger.error("No create_agent available and no module-level agent imported. Cannot create agent.")
        else:
            try:
                logger.info("Creating agent via create_agent() (lazy).")
                agent_obj = create_agent()
                logger.info("Lazy create_agent() succeeded.")
            except Exception:
                logger.exception("create_agent() failed.")

    if agent_obj is None:
        logger.warning("No agent available. Will display direct tool outputs and stop.")
        handler.flush()
        st.subheader("Direct tool outputs")
        for k, v in direct_results.items():
            st.markdown(f"**{k}**")
            st.code(v[:2000])
        st.subheader("Logs")
        handler.flush()
        st.text_area("Logs", log_stream.getvalue(), height=350)
    else:
        # Introspect agent
        try:
            inner = getattr(agent_obj, "inner", agent_obj)
            if hasattr(inner, "input_keys"):
                logger.info("Agent inner.input_keys: %s", inner.input_keys)
            if hasattr(inner, "allowed_tools"):
                logger.info("Agent inner.allowed_tools: %s", inner.allowed_tools)
            if hasattr(inner, "agent") and hasattr(inner.agent, "allowed_tools"):
                logger.info("Agent.agent.allowed_tools: %s", inner.agent.allowed_tools)
        except Exception:
            logger.debug("Agent introspection failed (not critical).", exc_info=True)

        # print prompt template if available
        try_print_agent_prompt(agent_obj)

        # Try running the agent with provided prompt (safe attempts)
        logger.info("=== AGENT RUN TEST ===")
        agent_output = None
        try:
            agent_output = safe_agent_run(agent_obj, prompt)
            logger.info("Agent returned successfully.")
        except Exception:
            logger.exception("Agent run failed. Will fallback to direct StockNewsTool call.")

        # Render results
        st.subheader("Direct tool outputs")
        for k, v in direct_results.items():
            st.markdown(f"**{k}**")
            st.code(v[:2000])

        st.subheader("Agent run output (if any)")
        if agent_output:
            # sometimes LC returns dict-like objects
            if isinstance(agent_output, dict):
                st.json(agent_output)
            else:
                st.code(agent_output[:10000])
        else:
            st.info("Agent run failed — fallback will be invoked below.")

        # fallback: extract ticker and call StockNewsTool directly
        if not agent_output:
            symbol = extract_symbol_simple(prompt)
            if not symbol:
                logger.error("Could not extract symbol from prompt for fallback.")
                st.error("Fallback failed: no ticker found in prompt.")
            else:
                logger.info("Fallback: calling StockNewsTool directly with symbol: %s", symbol)
                tool = find_tool("StockNewsTool")
                if tool is None:
                    logger.error("StockNewsTool not available for fallback.")
                    st.error("Fallback failed: StockNewsTool missing.")
                else:
                    try:
                        fallback_out = tool.func({"symbol": symbol})
                        st.subheader("Fallback tool output")
                        st.code(str(fallback_out)[:20000])
                    except Exception:
                        logger.exception("Fallback tool call failed.")
                        st.error("Fallback tool call failed. See logs.")

        # show logs at the bottom
        handler.flush()
        st.subheader("Logs (debug)")
        st.text_area("Logs", log_stream.getvalue(), height=500)

# small note
st.caption("Chatbot test page using LangChain agent with StockNewsTool.")