"""End-to-end test of the Exemplar SDK's **Eval & Run ingestion** capability,
run against the REAL trading_agent (ADK -> LiteLLM -> Ollama + TradingView MCP).

Flow:
  1. Run the trading agent for one real turn (real LLM call + real MCP tool).
  2. Ingest that turn into the Exemplar platform via `harness.ingest(...)`
     with auto_judge_run=True, auto_session_eval=True.
  3. Read the session back (`harness.sessions.get`).
  4. Trigger + poll the LLM judge (`harness.runs`) and print the judgement.

Prereqs (already running on this machine):
  - integration-service on :8000  (EXEMPLAR_BASE_URL)
  - agent-service on :8083        (the LLM judge; Gemini via GOOGLE_API_KEY)
  - Ollama on :11434
  - tradingview-mcp venv at D:\\tradingview-mcp

This is a throwaway test script - safe to delete after.
"""

import asyncio
import json
import os
import pathlib
import sys
import time
import uuid


# --- load .env (same minimal loader as agent.py) ---
def _load_dotenv() -> None:
    p = pathlib.Path(__file__).resolve().parent / ".env"
    if not p.exists():
        return
    for _line in p.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, v = _line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

import exemplar_harness  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from trading_agent.agent import mcp_toolset, root_agent  # noqa: E402
from trading_agent.config import GLM_MODEL  # noqa: E402

AGENT_ID = "trading-agent"
SOURCE_APP = "agents-testting"
QUERY = "Give me a BINANCE 1h market snapshot."


async def run_agent_one_turn(query: str) -> tuple[str, list[str]]:
    """Run the trading agent for one turn; return (final_text, tool_calls)."""
    runner = InMemoryRunner(agent=root_agent, app_name="trading_agent")
    session = await runner.session_service.create_session(
        app_name="trading_agent", user_id="eval_user"
    )
    message = types.Content(role="user", parts=[types.Part(text=query)])
    final_text = ""
    tool_calls: list[str] = []
    try:
        async for event in runner.run_async(
            user_id="eval_user", session_id=session.id, new_message=message
        ):
            if not (event.content and event.content.parts):
                continue
            for part in event.content.parts:
                if part.function_call and part.function_call.name:
                    tool_calls.append(part.function_call.name)
                if part.text:
                    final_text = part.text  # keep the last text part (final answer)
    finally:
        await mcp_toolset.close()
    return final_text, tool_calls


def _pretty(d) -> str:
    try:
        return json.dumps(d, indent=2, default=str)[:4000]
    except Exception:
        return str(d)[:4000]


def _extract_id(d: dict) -> str | None:
    for k in ("savedResultId", "resultId", "runId", "judgementId", "id", "result_id", "run_id"):
        v = d.get(k)
        if isinstance(v, str) and v:
            return v
    return None


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    print("== 1. Run the real trading agent for one turn ==")
    final_text, tool_calls = asyncio.run(run_agent_one_turn(QUERY))
    print(f"query : {QUERY}")
    print(f"tools : {tool_calls}")
    preview = (final_text or "").replace("\n", " ")
    print(f"reply : {preview[:300]}{'...' if len(final_text) > 300 else ''}")
    if not final_text:
        print("WARN: agent returned no final text; proceeding with empty output.")

    print("\n== 2. init harness + ingest the turn (auto_judge_run=True) ==")
    harness = exemplar_harness.init(agent_id=AGENT_ID)
    # Sync judge run (int-svc -> agent-service -> Gemini) outlasts the SDK's 30s
    # default HTTP timeout; the server-side sync cap is 600s, so bump the client.
    harness._client._timeout = 180.0
    print(f"base_url : {harness.base_url}")

    sid = f"eval-{uuid.uuid4().hex[:12]}"
    # Build a toolTrace from the captured tool calls (count occurrences) so the
    # judge's cost/efficiency detectors have something to analyze. Without a
    # toolTrace the judge (token-efficiency / rate-limit / budget /
    # agent-skills / context-optimization skills) finds nothing actionable and
    # returns 0 insights -- which is correct behavior, not a bug.
    from collections import Counter
    tool_trace = " · ".join(f"{name} x{count}" for name, count in Counter(tool_calls).items()) or None
    print(f"toolTrace : {tool_trace}")
    turn_data = {
        "turns": [
            {
                "input": QUERY,
                "output": final_text or "(no response)",
                "model": GLM_MODEL,
                "toolTrace": tool_trace,
            }
        ],
        "agentId": AGENT_ID,
    }
    ingest_resp = harness.ingest(
        "generic",
        session_id=sid,
        event="turns",
        data=turn_data,
        source_app=SOURCE_APP,
        agent_id=AGENT_ID,
        auto_judge_run=True,
        auto_session_eval=True,
    )
    print(f"session_id : {sid}")
    print("ingest response:")
    print(_pretty(ingest_resp))

    print("\n== 3. Read the session back (harness.sessions.get) ==")
    sess = harness.sessions.get(sid)
    print(_pretty(sess))

    print("\n== 4. Trigger + poll the LLM judge (harness.runs) ==")
    # auto_judge_run on ingest already enqueued a judge; trigger sync too so we
    # get an immediate result_id we can poll.
    trig = harness.runs.trigger(session_ids=[sid], sync=True, force=True)
    print("trigger response:")
    print(_pretty(trig))
    result_id = _extract_id(trig) or _extract_id(ingest_resp)
    if not result_id:
        print("No result_id found in trigger/ingest response; cannot poll judgement.")
        return

    print(f"\npolling judgement {result_id} ...")
    j: dict = {}
    for i in range(20):
        time.sleep(3)
        try:
            j = harness.runs.get(result_id)
        except Exception as exc:
            print(f"  [{i + 1:02d}] get failed: {exc}")
            continue
        status = j.get("status") or j.get("state") or "???"
        print(f"  [{i + 1:02d}] status={status}")
        if str(status).lower() in (
            "complete",
            "completed",
            "done",
            "success",
            "failed",
            "error",
        ):
            break
    print("\njudgement:")
    print(_pretty(j))


if __name__ == "__main__":
    main()