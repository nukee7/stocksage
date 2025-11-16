#!/usr/bin/env python3
"""
Test harness for your LangChain agent (news-only usage).

Behavior:
- Shows available tools.
- Runs a direct call to StockNewsTool (dict / string inputs).
- Attempts to run the agent in multiple ways to be compatible with LangChain versions:
    1) agent.run(prompt)
    2) agent(prompt)  (callable)
    3) agent({"input": prompt})
- If the agent calls fail, it falls back to extracting a ticker and calling StockNewsTool.func directly.

This script is defensive — it logs introspection info that helps debug input-key / template mismatches.
"""
import json
import logging
import traceback
from typing import Any, Dict, Optional

# Import your agent & tools
try:
    from backend.langchain_core.utils.agent_builder import agent as agent_builder_agent
    from backend.langchain_core.utils.agent_builder import create_agent
except Exception:
    # If module-level creation failed earlier, import function only to lazily create agent later.
    agent_builder_agent = None
    try:
        from backend.langchain_core.utils.agent_builder import create_agent  # type: ignore
    except Exception:
        create_agent = None  # type: ignore

from backend.langchain_core.utils.tools_config import tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROMPT = "Show me the latest news for AAPL"


def find_tool(name: str):
    for t in tools:
        if getattr(t, "name", None) == name:
            return t
    return None


def extract_symbol_simple(prompt: str) -> Optional[str]:
    """Very simple ticker extractor (uppercase words 1-5 chars)."""
    for token in prompt.replace(",", " ").split():
        tok = token.strip().upper()
        if tok.isalpha() and 1 <= len(tok) <= 5:
            # crude check: skip common words that aren't tickers
            if tok in {"SHOW", "ME", "THE", "LATEST", "NEWS", "FOR"}:
                continue
            return tok
    return None


def try_print_agent_prompt(agent_obj: Any):
    """Attempt to print agent prompt template (works on many LangChain versions)."""
    try:
        inner = getattr(agent_obj, "inner", agent_obj)
        # try a few known attribute paths
        prompt = None
        if hasattr(inner, "agent") and hasattr(inner.agent, "llm_chain"):
            prompt = getattr(inner.agent.llm_chain, "prompt", None)
        if prompt is None and hasattr(inner, "llm_chain"):
            prompt = getattr(inner.llm_chain, "prompt", None)
        if prompt is not None:
            tmpl = getattr(prompt, "template", None)
            if tmpl:
                logger.info("Found agent prompt template (truncated):\n%s", (tmpl[:1000] + "...") if len(tmpl) > 1000 else tmpl)
            else:
                logger.info("Agent prompt object found but has no .template attribute.")
        else:
            logger.info("Could not find agent prompt object on agent (different langchain internals).")
    except Exception:
        logger.exception("Error while trying to read agent prompt template.")


def safe_agent_run(agent_obj: Any, prompt_text: str) -> str:
    """
    Try several agent invocation patterns for compatibility.
    Returns the agent result string or raises last exception.
    """
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

    # 3) agent({"input": prompt_text})
    try:
        logger.info("Attempting agent({'input': prompt}) ...")
        out = agent_obj({"input": prompt_text})
        logger.info("agent({'input': prompt}) succeeded.")
        return str(out)
    except Exception as e:
        attempts.append(("agent({'input': prompt})", e))
        logger.warning("agent({'input': prompt}) failed: %s", e)

    # 4) Try positional run via .__call__ with dict that some versions expect
    try:
        logger.info("Attempting agent.__call__({'input': prompt}) ...")
        out = agent_obj.__call__({"input": prompt_text})
        logger.info("agent.__call__ succeeded.")
        return str(out)
    except Exception as e:
        attempts.append(("agent.__call__", e))
        logger.warning("agent.__call__ failed: %s", e)

    # If all failed, raise the last exception
    last_name, last_exc = attempts[-1]
    logger.error("All agent invocation attempts failed. Attempts: %s", [n for n, _ in attempts])
    raise last_exc


def direct_tool_test():
    """Call StockNewsTool directly with a few different input shapes."""
    logger.info("=== DIRECT TOOL TEST ===")
    tool = find_tool("StockNewsTool")
    if tool is None:
        logger.error("StockNewsTool not found in configured tools.")
        return

    test_inputs = [
        {"symbol": "AAPL"},
        '"AAPL"',  # JSON string representation (commonly accepted by some wrappers)
        "AAPL",    # plain string
    ]

    for i, inp in enumerate(test_inputs, start=1):
        try:
            logger.info("Direct call #%d with input: %s", i, inp)
            out = tool.func(inp)
            if isinstance(out, str) and len(out) > 500:
                logger.info("Output (first 500 chars): %s", out[:500])
            else:
                logger.info("Output: %s", str(out)[:1000])
        except Exception:
            logger.exception("Direct tool call #%d failed.", i)


def main():
    logger.info("Device set to use mps:0")
    logger.info("INFO:backend.model.portfolio_model:Portfolio initialized with $100,000.00")

    # Show configured tools
    try:
        tool_names = [t.name for t in tools]
    except Exception:
        tool_names = [getattr(t, "name", str(t)) for t in tools]
    logger.info("Configured tools: %s", tool_names)

    # Direct tool test
    direct_tool_test()

    # Ensure we have an agent object to test. If the module-level agent failed to import,
    # try to create one lazily (create_agent).
    agent_obj = agent_builder_agent
    if agent_obj is None:
        if create_agent is None:
            logger.error("No create_agent available and no module-level agent imported. Cannot test agent.")
        else:
            try:
                logger.info("Creating agent via create_agent() (lazy).")
                agent_obj = create_agent()
            except Exception:
                logger.exception("create_agent() failed.")

    if agent_obj is None:
        logger.info("No agent available. Exiting after direct tool test.")
        return

    # Introspect agent if possible
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

    # Try printing agent prompt template (best-effort — may not exist on your LangChain version)
    try_print_agent_prompt(agent_obj)

    # Try running the agent with the simple prompt
    logger.info("=== AGENT RUN TEST ===")
    try:
        result = safe_agent_run(agent_obj, PROMPT)
        logger.info("Agent run result (truncated 4000 chars):\n%s", (result[:4000] + "...") if len(result) > 4000 else result)
        print("\n\n=== AGENT OUTPUT ===\n")
        print(result)
    except Exception:
        logger.exception("Agent run failed. Falling back to direct StockNewsTool call.")

        # fallback: extract ticker and call the tool directly
        symbol = extract_symbol_simple(PROMPT)
        if not symbol:
            logger.error("Could not extract symbol from prompt for fallback.")
            print("Fallback failed: no ticker found in prompt.")
            return

        logger.info("Fallback: calling StockNewsTool directly with symbol: %s", symbol)
        tool = find_tool("StockNewsTool")
        if tool is None:
            logger.error("StockNewsTool not available for fallback.")
            print("Fallback failed: StockNewsTool not found.")
            return

        try:
            out = tool.func({"symbol": symbol})
            print("\n\n=== FALLBACK TOOL OUTPUT ===\n")
            print(out[:10000])  # print a generous preview
        except Exception:
            logger.exception("Fallback tool call failed.")
            print("Fallback failed with exception. See logs.")


if __name__ == "__main__":
    main()