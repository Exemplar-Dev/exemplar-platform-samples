# --- Exemplar Cost Observability: attach once, works however you run this agent ---
# (adk web / adk run / python trading_agent/cli.py / tests — every LLM call observed.)
# Fails open: if the SDK isn't configured (e.g. EXEMPLAR_API_KEY missing from .env),
# the agent still runs normally — you just don't get observability until it's set.
import os
import pathlib


def _load_dotenv() -> None:
    """Tiny .env loader (no dependency) so the SDK works outside ADK's own runner."""
    p = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if not p.exists():
        return
    for _line in p.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, v = _line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()
# auto_instrument captures composition + usage + per-tool + history-dup + RAG
# via the genai monkey-patch (covers ADK-on-Gemini natively). The report is
# captured so the harness is reachable for harness.session(...) scoping below.
# The orchestration counters (llmCalls / retries / toolCallCounts / ...) are a
# SEPARATE concern: the genai patch never emits an orchestration summary, so
# retry-storm + repeated-tool-calls can't fire under auto alone. We attach the
# ADK orchestration handler (counting-only, coexists with the genai patch) to
# root_agent and flush its summary once per run inside harness.session(...) —
# see cli.py / run_detectors_live.py. Both fail open: if the SDK is unconfigured
# (e.g. EXEMPLAR_API_KEY missing from .env) the agent still runs normally.
_exemplar_report = None
_orch = None
try:
    import exemplar_harness  # pyright: ignore[reportMissingImports] # type: ignore
    _exemplar_report = exemplar_harness.auto_instrument(
        agent_id="trading-agent", source_app="agents-testting"
    )
    from exemplar_harness.integrations.context_observer.google_adk_orchestration import (
        make_google_adk_orchestration_handler,
    )

    # Dynamic-observer path: no fixed observer -> record_run_summary() resolves
    # current_observer() at flush time, so orchestration lands on the SAME
    # session as the composition events the genai patch recorded (no split).
    _orch = make_google_adk_orchestration_handler(
        agent_id="trading-agent", source_app="agents-testting"
    )
    print(f"[exemplar-harness] is active (composition + ADK orchestration)")
except Exception as _e:  # never break the agent if the SDK is unconfigured
    print(f"[exemplar-harness] not active: {_e}")
# -------------------------------------------------------------------------------

from google.adk.agents import LlmAgent
from google.adk.models import Gemini

from trading_agent.prompts import INSTRUCTION
from trading_agent.rag import search_knowledge_base
from trading_agent.tools import create_mcp_toolset

mcp_toolset = create_mcp_toolset()
model = Gemini(model="gemini-2.5-pro")

_agent_kwargs = dict(
    name="trading_agent",
    model=model,
    description="Market analysis assistant backed by TradingView MCP and a Voyage AI RAG knowledge base.",
    instruction=INSTRUCTION,
    tools=[mcp_toolset, search_knowledge_base],
)
# Attach the orchestration callbacks when the handler was built. ADK reads these
# as the canonical per-agent callback fields; the genai patch handles composition
# inside the model call, so the two never double-observe.
if _orch is not None:
    _agent_kwargs.update(
        before_model_callback=_orch.before_model_callback,
        after_model_callback=_orch.after_model_callback,
        before_tool_callback=_orch.before_tool_callback,
        after_tool_callback=_orch.after_tool_callback,
        on_model_error_callback=_orch.on_model_error_callback,
        on_tool_error_callback=_orch.on_tool_error_callback,
    )

root_agent = LlmAgent(**_agent_kwargs)