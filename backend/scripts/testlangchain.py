#!/usr/bin/env python3
"""
Simple test runner that loads tools_config.py directly from file path.
Run from project root with:
    python backend/scripts/testlangchain.py
"""

import importlib.util
from pathlib import Path
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROMPT = "Show me the latest news for AAPL"

# Path to this file
THIS_FILE = Path(__file__).resolve()

# Correct path to tools_config.py:
TOOLS_CONFIG_PATH = (
    THIS_FILE.parents[1]              # -> backend/
    / "langchain_core"
    / "utils"
    / "tools_config.py"
)

def load_module_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_tool(tools, name: str):
    for t in tools:
        if getattr(t, "name", None) == name:
            return t
    return None


def extract_symbol(prompt: str):
    words = prompt.upper().replace("?", "").split()
    for w in words:
        if w.isalpha() and 1 <= len(w) <= 5:
            return w
    return None


def main():
    logger.info("Device set to use mps:0")
    logger.info("INFO:backend.model.portfolio_model:Portfolio initialized with $100,000.00")

    # Validate path
    if not TOOLS_CONFIG_PATH.exists():
        logger.error("tools_config.py NOT FOUND at: %s", TOOLS_CONFIG_PATH)
        sys.exit(2)

    logger.info(f"Loading tools_config from: {TOOLS_CONFIG_PATH}")

    # Load tools_config.py without importing backend package
    tools_mod = load_module_from_path("tools_config_local", TOOLS_CONFIG_PATH)
    tools = getattr(tools_mod, "tools", None)

    if tools is None:
        logger.error("'tools' list not found in tools_config.py")
        sys.exit(3)

    logger.info("Loaded tools: %s", [t.name for t in tools])

    symbol = extract_symbol(PROMPT)
    if not symbol:
        logger.error("No symbol extracted from prompt.")
        sys.exit(4)

    logger.info(f"Extracted symbol: {symbol}")

    stock_news_tool = find_tool(tools, "StockNewsTool")
    if not stock_news_tool:
        logger.error("StockNewsTool not found in tools list.")
        sys.exit(5)

    logger.info("Calling StockNewsTool...")
    result = stock_news_tool.func({"symbol": symbol})

    print("\n=== RESULT ===\n")
    print(result[:4000])  # preview


if __name__ == "__main__":
    main()