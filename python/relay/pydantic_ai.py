"""Live Relay + Pydantic AI before/after tool hooks."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exemplar_harness.relay.adapters.pydantic_ai import build_pydantic_ai_hooks

from common import SOURCE_APP, harness, session_id  # noqa: E402


class _Call:
    def __init__(self, name: str, call_id: str = "tc-1") -> None:
        self.tool_name = name
        self.tool_call_id = call_id


async def _exercise(before, after) -> dict:
    allowed_args = await before(call=_Call("get_weather"), args={"city": "SF"})
    await after(call=_Call("get_weather"), args={"city": "SF"}, result="Sunny")
    denied = False
    deny_reason = None
    try:
        await before(call=_Call("shell"), args={"command": "rm -rf /tmp/x"})
    except Exception as exc:
        denied = True
        deny_reason = str(exc)
    return {
        "exerciseMode": "callables",
        "allowedArgs": allowed_args,
        "denied": denied,
        "denyReason": deny_reason,
    }


def main() -> None:
    h = harness("relay-pydantic-ai-sample")
    sid = session_id("relay-pydantic-ai")
    relay = h.relay(surface="pydantic_ai", source_app=SOURCE_APP)
    hooks = relay.pydantic_ai_hooks(session_id=sid)

    if isinstance(hooks, dict):
        result = asyncio.run(
            _exercise(hooks["before_tool_execute"], hooks["after_tool_execute"])
        )
    else:
        raw = build_pydantic_ai_hooks(relay, session_id=sid)
        if isinstance(raw, dict):
            result = asyncio.run(
                _exercise(raw["before_tool_execute"], raw["after_tool_execute"])
            )
        else:
            safe = relay.evaluate(
                tool_name="get_weather",
                arguments={"city": "SF"},
                session_id=sid,
            )
            blocked = relay.evaluate(
                tool_name="shell",
                arguments={"command": "rm -rf /tmp/x"},
                session_id=sid,
            )
            result = {
                "exerciseMode": "hooks_object",
                "hooksType": type(hooks).__name__,
                "safe": str(safe.decision),
                "blocked": str(blocked.decision),
            }

    print(
        json.dumps(
            {
                "example": "relay_pydantic_ai",
                "sessionId": sid,
                **result,
                "wire": "Agent(..., capabilities=[relay.pydantic_ai_hooks(session_id=...)])",
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
