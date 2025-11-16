# backend/service/chatbot_service.py
import logging
from backend.langchain_core.utils.agent_builder import create_agent

logger = logging.getLogger(__name__)
_agent = None

# Helper: a conservative "retry" system prompt to avoid mixed action+final outputs
RETRY_PREFIX = (
    "SYSTEM INSTRUCTION (for this retry only): When you decide to CALL A TOOL, "
    "ONLY output the ACTION block (Action: <ToolName> / Action Input: ...). "
    "DO NOT include any 'Final Answer' or explanatory text in the same response. "
    "Wait for the tool output before producing a final answer.\n\n"
)

def run_chatbot(query: str):
    """
    Run the LangChain agent using positional .run() calls only (compatible with this LangChain version).
    If the agent raises an output-parsing error, retry once with an explicit instruction to the model.
    """
    global _agent
    if _agent is None:
        _agent = create_agent()

    prompt = str(query)

    try:
        # Call with positional arg only (no kwargs) — compatible across versions
        return _agent.run(prompt)
    except ValueError as e:
        # LangChain raises ValueError for parsing-related failures in some versions
        msg = str(e).lower()
        logger.exception("Agent run failed on first attempt.")

        # If this looks like an output parsing problem, do a single retry with stricter instructions
        if "parsing" in msg or "output parsing" in msg or "parse" in msg:
            try:
                retry_prompt = RETRY_PREFIX + prompt
                logger.info("Retrying agent with clearer instruction to avoid final answers with actions.")
                return _agent.run(retry_prompt)  # positional-only call on retry
            except Exception as e2:
                logger.exception("Agent failed on retry after parsing error.")
                return "Sorry — the assistant had trouble formatting its response. Please try rephrasing."

        # If it's not obviously a parsing error, re-raise or return friendly fallback
        logger.exception("Agent run failed with ValueError (not recognized as parsing error).")
        return "Sorry — I couldn't complete that request. Please try again."

    except Exception as exc:
        # Any other unexpected exception
        logger.exception("Agent run failed with an unexpected error.")
        return "Sorry — something went wrong. Please try again."