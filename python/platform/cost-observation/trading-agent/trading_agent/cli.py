import asyncio
import sys
import uuid

from google.adk.runners import InMemoryRunner
from google.genai import types

from trading_agent.agent import _exemplar_report, _orch, mcp_toolset, root_agent
from trading_agent.config import CLI_OUTPUT_LIMIT


def shorten_text(text: str, limit: int = CLI_OUTPUT_LIMIT) -> str:
    text = text.replace("\\n", "\n")
    return text if len(text) <= limit else text[:limit] + f"\n…[+{len(text) - limit} chars]"

async def run_cli(query: str) -> None:
    runner = InMemoryRunner(agent=root_agent, app_name="trading_agent")
    session = await runner.session_service.create_session(
        app_name="trading_agent", user_id="cli_user"
    )
    message = types.Content(
        role="user", parts=[types.Part(text=query)]
    )
    # Scope this run to its own exemplar session so composition + orchestration
    # land on ONE session (the orch handler resolves current_observer() to this
    # scope's observer at flush time). Per-run sessions are also what the
    # oversized-system-prompt cross-session detector needs (>=2 runs of the same
    # agent). Falls open when the SDK is inactive (_exemplar_report is None).
    exemplar_session_id = f"trade-cli-{uuid.uuid4().hex[:8]}"
    _scope = (
        _exemplar_report.harness.session(
            agent_id="trading-agent",
            session_id=exemplar_session_id,
            source_app="agents-testting",
        )
        if _exemplar_report is not None
        else None
    )
    try:
        if _scope is not None:
            _scope.__enter__()
        try:
            async for event in runner.run_async(
                user_id="cli_user", session_id=session.id, new_message=message
            ):
                if not (event.content and event.content.parts):
                    continue
                final = getattr(event, "is_final_response", lambda: False)()
                tag = f"{event.author}" + (" [FINAL]" if final else "")
                for i, part in enumerate(event.content.parts):
                    if part.text:
                        print(f"{tag}: {part.text}")
                    elif part.function_call:
                        args = dict(part.function_call.args or {})
                        print(f"{tag}: [call] {part.function_call.name}({args})")
                    elif part.function_response:
                        resp = part.function_response.response
                        print(f"{tag}: [resp] {part.function_response.name}:")
                        print(shorten_text(str(resp)))
                    else:
                        print(f"{tag}: <part {i} {part!r}>")
        finally:
            # Flush the orchestration summary INSIDE the session scope so
            # current_observer() resolves to this run's observer. No-op when
            # the handler is inactive or the run had no LLM calls.
            if _orch is not None:
                _orch.record_run_summary()
    finally:
        if _scope is not None:
            _scope.__exit__(None, None, None)
        await mcp_toolset.close()


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    query = " ".join(sys.argv[1:]).strip() or "Give me a BINANCE 1h market snapshot."
    asyncio.run(run_cli(query))


if __name__ == "__main__":
    main()