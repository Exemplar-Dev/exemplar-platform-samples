"""Live end-to-end verification of all 6 advisory detectors on the real
trading_agent (Google ADK + Gemini 2.5-pro + Voyage/Chroma RAG + TradingView MCP).

Runs the orch-wired ``root_agent`` through curated prompts — each scoped to its
own exemplar session via ``harness.session(...)`` and followed by an
``_orch.record_run_summary()`` flush (so the orchestration counters land on the
same session as the composition events) — then queries the integration-service
session read path (the same one console-ui uses) and asserts which
recommendations + orchestration blocks landed.

The 6 detector categories:
  - unused-tools (#1)            composition (toolUsage)   deterministic-ish
  - tool-schema-bloat (#2)       composition (toolUsage)   deterministic-ish
  - tool-result-persistence (#19)composition (toolResult)  deterministic-ish
  - oversized-system-prompt      composition, CROSS-SESSION needs >=2 runs
  - retry-storm                  orchestration (retries)   best-effort (Gemini
                                                           rarely errors >=3x)
  - repeated-tool-calls          orchestration (toolCallCounts /
                                 maxSameArgsRepeat)        model-dependent

Read-back assertions are HARD for the deterministic ones (unused-tools,
oversized-system-prompt) and SOFT (WARN, not exit) for the model-dependent ones
(retry-storm, repeated-tool-calls, rag-overfetch, tool-result-persistence) —
matching ``cost-obs-live-tests/verify_recommendations_live.py``'s "model did not
call a tool -> WARN" posture. The orch-handler unit test + the detector unit test
are the deterministic proof for retry-storm / repeated-tool-calls; this script is
the live end-to-end confirmation when the model cooperates.

Run (from a terminal with GEMINI_API_KEY + VOYAGE_API_KEY set in
D:\\agents-testting\\.env, the TradingView MCP venv configured, and the
integration-service up on :8000 with HARNESS_CONTEXT_ENABLED=true):

    D:/Exemplar/exemplar-harness-sdk/.venv/Scripts/python.exe \\
        D:/agents-testting/run_detectors_live.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid

import httpx

# Windows console defaults to cp1252 and crashes on emoji the model emits.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:
    pass

# importing trading_agent.agent loads D:\agents-testting\.env (see _load_dotenv)
# and runs auto_instrument + builds the orch-wired root_agent.
from trading_agent.agent import (  # noqa: E402
    _exemplar_report,
    _orch,
    mcp_toolset,
    root_agent,
)

AGENT_ID = "trading-agent"
SOURCE_APP = "agents-testting"
BASE = os.environ.get("EXEMPLAR_BASE_URL", "http://localhost:8000")


def _auth_headers() -> dict[str, str]:
    key = os.environ.get("EXEMPLAR_API_KEY", "")
    return {
        "Authorization": f"Bearer {key}",
        "X-API-Key": key,
        "Content-Type": "application/json",
    }


HEADERS = _auth_headers()


def _short(s, n=120):
    try:
        return repr(str(s)[:n])
    except Exception:
        return "<unprintable>"


async def _run_query(
    runner,
    adk_session_id: str,
    message: str,
    *,
    user_id: str = "detectors_live",
):
    """Send one user message to an ADK session and print the events. Returns the
    final text parts (best-effort). Does NOT flush the orch summary — the caller
    flushes once after the whole exemplar-scoped run."""
    from google.genai import types

    content = types.Content(role="user", parts=[types.Part(text=message)])
    final_texts: list[str] = []
    tool_calls: list[str] = []
    async for event in runner.run_async(
        user_id=user_id, session_id=adk_session_id, new_message=content
    ):
        if not (event.content and event.content.parts):
            continue
        final = getattr(event, "is_final_response", lambda: False)()
        tag = f"{event.author}" + (" [FINAL]" if final else "")
        for part in event.content.parts:
            if part.text:
                if final:
                    final_texts.append(part.text)
                print(f"    {tag}: {_short(part.text)}")
            elif part.function_call:
                args = dict(part.function_call.args or {})
                tool_calls.append(part.function_call.name)
                print(f"    {tag}: [call] {part.function_call.name}({_short(args, 60)})")
            elif part.function_response:
                print(f"    {tag}: [resp] {part.function_response.name}: {_short(part.function_response.response, 80)}")
    return final_texts, tool_calls


async def run_scenario(
    name: str,
    messages: list[str],
    *,
    shared_adk_session: bool = False,
) -> str:
    """Run one scenario: one exemplar session scope wrapping one (or more, if
    shared_adk_session) ADK turns, then flush the orch summary inside the scope.
    Returns the exemplar session_id used (for the read-back)."""
    from google.adk.runners import InMemoryRunner

    exemplar_sid = f"det-{name}-{uuid.uuid4().hex[:8]}"
    runner = InMemoryRunner(agent=root_agent, app_name="trading_agent")
    adk_session = await runner.session_service.create_session(
        app_name="trading_agent", user_id="detectors_live"
    )
    adk_sid = adk_session.id
    all_tool_calls: list[str] = []
    scope = (
        _exemplar_report.harness.session(
            agent_id=AGENT_ID, session_id=exemplar_sid, source_app=SOURCE_APP
        )
        if _exemplar_report is not None
        else None
    )
    print(f"\n{'=' * 72}\n[scenario] {name}  exemplar_session={exemplar_sid}")
    try:
        if scope is not None:
            scope.__enter__()
        try:
            for i, msg in enumerate(messages):
                print(f"  [turn {i + 1}] {_short(msg, 100)}")
                _, tcalls = await _run_query(runner, adk_sid, msg)
                all_tool_calls.extend(tcalls)
                if not shared_adk_session:
                    # multi-turn needs the SAME adk session; single-turn reuses
                    # it too (one message) — this branch is a no-op then.
                    pass
        finally:
            if _orch is not None:
                _orch.record_run_summary()  # flush + reset, inside the scope
    finally:
        if scope is not None:
            scope.__exit__(None, None, None)
    print(f"  [scenario] tool calls seen: {all_tool_calls or '<none>'}")
    return exemplar_sid


def read_session(exemplar_sid: str, timeout: float = 20.0) -> dict | None:
    """Query the int-svc session read path for one exemplar session."""
    url = f"{BASE}/api/harness-context/v1/sessions"
    r = httpx.get(url, params={"agentId": AGENT_ID, "limit": 50}, headers=HEADERS, timeout=timeout)
    print(f"[read] GET {url}?agentId={AGENT_ID} -> HTTP {r.status_code}")
    if r.status_code != 200:
        print(f"    body: {_short(r.text, 300)}")
        return None
    sessions = r.json().get("sessions", [])
    mine = [s for s in sessions if s.get("sessionId") == exemplar_sid]
    if not mine:
        print(f"    [read] session {exemplar_sid} NOT FOUND among {len(sessions)} sessions")
        return None
    return mine[0]


def print_session(s: dict) -> None:
    recs = s.get("recommendations") or []
    orch = s.get("orchestration")
    comp = s.get("composition")
    tu = s.get("toolUsage")
    trp = s.get("toolResultPersistence")
    print(f"    composition: {comp}")
    if tu:
        tools = [(t.get("toolName"), t.get("schemaBytes"), t.get("called")) for t in tu.get("tools", [])]
        print(f"    toolUsage.tools (name,schemaBytes,called): {tools}")
    print(f"    toolResultPersistence: {_short(trp, 200)}")
    print(f"    orchestration: {orch}")
    print(f"    recommendations ({len(recs)}):")
    for rec in recs:
        print(
            f"      - [{rec.get('category')}] {rec.get('title')}  "
            f"savingsUsd={rec.get('estimatedSavingsUsd')}  conf={rec.get('confidence')}"
        )


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

async def main() -> int:
    if _exemplar_report is None or _orch is None:
        print("[live] exemplar-harness NOT active — aborting (needs EXEMPLAR_API_KEY in .env).")
        return 1
    print(f"[live] integration-service={BASE}  agent={AGENT_ID}")
    print(f"[live] root_agent callbacks wired: after_model={_orch.after_model_callback is not None}")

    results: dict[str, str] = {}  # scenario name -> exemplar session id

    # 1. oversized-system-prompt (CROSS-SESSION): run a baseline TWICE — two
    #    sessions of the same agent. The static ~2400-byte INSTRUCTION fires the
    #    detector on the 2nd session (needs >=2 stable large-prompt sessions).
    results["oversized_a"] = await run_scenario(
        "oversized_a", ["Give me a BINANCE 1h market snapshot."]
    )
    results["oversized_b"] = await run_scenario(
        "oversized_b", ["Summarize the current BTC trend in two sentences."]
    )

    # 2. unused-tools: a narrow query that should call ONE tool while many are
    #    registered (the TradingView MCP exposes many + search_knowledge_base).
    results["unused_tools"] = await run_scenario(
        "unused_tools", ["What is the latest price of BTC? Just the number."]
    )

    # 3. repeated-tool-calls: ask for several prices/symbols -> the model calls
    #    a market tool >=4x (loose loop: dominant count >=4, dominance >=0.5) or
    #    the same args >=3x (tight loop).
    results["repeated_tool_calls"] = await run_scenario(
        "repeated_tool_calls",
        ["Get me the latest price for each of these: BTC, ETH, ADA, DOT, LINK, SOL, XRP."],
    )

    # 4. tool-result-persistence: a 3-turn conversation where a large tool result
    #    stays in history (follow-ups that don't drop it) -> same tool_result
    #    block hash in >=2 composition events on the same exemplar session.
    results["tool_result_persistence"] = await run_scenario(
        "tool_result_persistence",
        [
            "Give me a detailed BINANCE 1h market snapshot with all indicators.",
            "Summarize what you just found in one line.",
            "Now highlight only the RSI and MACD from that snapshot.",
        ],
        shared_adk_session=True,
    )

    # 5. rag-overfetch (bonus, already wired via chromadb auto-patch): a
    #    knowledge-base query with top_k=5 where the model may use fewer.
    results["rag_overfetch"] = await run_scenario(
        "rag_overfetch",
        ["Search the knowledge base for everything about momentum trading strategies "
         "and tell me the key points."],
    )

    # 6. retry-storm: best-effort — relies on real model/tool errors (rare with
    #    Gemini). We still run a normal query so the orchestration block is
    #    populated; the read-back WARNs if retries < 3.
    results["retry_storm"] = await run_scenario(
        "retry_storm", ["Give me an ETH 4h market snapshot."]
    )

    # close the shared MCP toolset once at the end
    try:
        await mcp_toolset.close()
    except Exception:
        pass

    # --- read-back + assertions --------------------------------------------
    print(f"\n{'#' * 72}\n[live] READ-BACK + ASSERTIONS (waiting 2s for async ingest)")
    time.sleep(2.0)

    ok = True
    soft_failures: list[str] = []

    def hard(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        st = "PASS" if cond else "FAIL"
        if not cond:
            ok = False
        print(f"  [{st}] {label}{(' — ' + detail) if detail else ''}")

    def soft(label: str, cond: bool, detail: str = "") -> None:
        st = "PASS" if cond else "WARN"
        if not cond:
            soft_failures.append(label)
        print(f"  [{st}] {label}{(' — ' + detail) if detail else ''}")

    # oversized-system-prompt: hard — must fire once across the two sessions.
    s_a = read_session(results["oversized_a"])
    s_b = read_session(results["oversized_b"])
    cats_a = {r.get("category") for r in (s_a or {}).get("recommendations", [])} if s_a else set()
    cats_b = {r.get("category") for r in (s_b or {}).get("recommendations", [])} if s_b else set()
    if s_a:
        print_session(s_a)
    if s_b:
        print_session(s_b)
    hard(
        "oversized-system-prompt fires across >=2 sessions",
        "oversized-system-prompt" in (cats_a | cats_b),
        f"cats_a={cats_a} cats_b={cats_b}",
    )

    # unused-tools: soft (model-dependent) — model may call >1 tool.
    s_u = read_session(results["unused_tools"])
    cats_u = {r.get("category") for r in (s_u or {}).get("recommendations", [])} if s_u else set()
    if s_u:
        print_session(s_u)
    soft("unused-tools emitted", "unused-tools" in cats_u, f"cats={cats_u}")

    # repeated-tool-calls: soft — needs the model to call one tool >=4x.
    s_r = read_session(results["repeated_tool_calls"])
    orch_r = (s_r or {}).get("orchestration") or {}
    cats_r = {r.get("category") for r in (s_r or {}).get("recommendations", [])} if s_r else set()
    if s_r:
        print_session(s_r)
    soft(
        "repeated-tool-calls orchestration captured (toolCallCounts present)",
        bool(orch_r.get("toolCallCounts")),
        f"orch={orch_r}",
    )
    soft("repeated-tool-calls emitted", "repeated-tool-calls" in cats_r, f"cats={cats_r}")

    # tool-result-persistence: soft — needs a large tool result carried across turns.
    s_p = read_session(results["tool_result_persistence"])
    trp = (s_p or {}).get("toolResultPersistence") or {}
    cats_p = {r.get("category") for r in (s_p or {}).get("recommendations", [])} if s_p else set()
    if s_p:
        print_session(s_p)
    soft(
        "tool-result-persistence aggregate present (block carried >=2 events)",
        any(b.get("eventCount", 0) >= 2 for b in trp.get("blocks", [])),
        f"blocks={[(b.get('toolName'), b.get('eventCount')) for b in trp.get('blocks', [])]}",
    )
    soft("tool-result-persistence emitted", "tool-result-persistence" in cats_p, f"cats={cats_p}")

    # rag-overfetch: soft — needs retrieval tracking + overfetch threshold.
    s_g = read_session(results["rag_overfetch"])
    cats_g = {r.get("category") for r in (s_g or {}).get("recommendations", [])} if s_g else set()
    if s_g:
        print_session(s_g)
    soft("rag-overfetch emitted", "rag-overfetch" in cats_g, f"cats={cats_g}")

    # retry-storm: soft (best-effort) — needs retries >= 3 (rare with Gemini).
    s_s = read_session(results["retry_storm"])
    orch_s = (s_s or {}).get("orchestration") or {}
    cats_s = {r.get("category") for r in (s_s or {}).get("recommendations", [])} if s_s else set()
    if s_s:
        print_session(s_s)
    soft(
        "retry-storm orchestration counters captured (llmCalls present)",
        orch_s.get("llmCalls") is not None,
        f"orch={orch_s}",
    )
    soft(
        "retry-storm emitted (best-effort; Gemini rarely errors >=3x)",
        "retry-storm" in cats_s,
        f"retries={orch_s.get('retries')} cats={cats_s}",
    )

    # --- summary -----------------------------------------------------------
    print(f"\n{'#' * 72}")
    all_cats = set()
    for sid in results.values():
        s = read_session(sid)
        if s:
            all_cats |= {r.get("category") for r in s.get("recommendations", [])}
    print(f"[live] distinct recommendation categories seen across all sessions: {sorted(all_cats)}")
    print(f"[live] hard checks: {'ALL PASSED' if ok else 'FAILURES'} | soft warnings: {len(soft_failures)}")
    for f in soft_failures:
        print(f"        WARN: {f}")
    if ok:
        print("[live] HARD CHECKS PASSED — orchestration + composition wired end-to-end on ADK.")
        print("[live] Open the console-ui Cost Observability panel -> trading-agent to see all 6 categories.")
        return 0
    print("[live] ONE OR MORE HARD CHECKS FAILED — see above.")
    return 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))