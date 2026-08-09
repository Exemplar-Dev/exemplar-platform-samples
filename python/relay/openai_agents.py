"""Live Relay + OpenAI Agents SDK tool input/output guardrails."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import SOURCE_APP, harness, session_id  # noqa: E402


class _Ctx:
    def __init__(self, tool_name: str, arguments: dict) -> None:
        self.tool_name = tool_name
        self.tool_arguments = arguments


class _Data:
    def __init__(self, tool_name: str, arguments: dict, output: object = None) -> None:
        self.context = _Ctx(tool_name, arguments)
        self.output = output


def _is_blocked(result: Any) -> bool:
    if isinstance(result, dict):
        return bool(result.get("tripwire_triggered"))
    if hasattr(result, "tripwire_triggered"):
        return bool(result.tripwire_triggered)
    name = type(result).__name__.lower()
    if "reject" in name:
        return True
    if "allow" in name:
        return False
    return False


def main() -> None:
    h = harness("relay-openai-agents-sample")
    sid = session_id("relay-openai-agents")
    relay = h.relay(surface="openai_agents", source_app=SOURCE_APP)
    on_input = relay.openai_tool_input(session_id=sid)
    on_output = relay.openai_tool_output(session_id=sid)

    allow = on_input(_Data("get_weather", {"city": "SF"}))
    deny = on_input(_Data("shell", {"command": "rm -rf /tmp/x"}))
    out = on_output(_Data("get_weather", {"city": "SF"}, output="Sunny"))

    print(
        json.dumps(
            {
                "example": "relay_openai_agents",
                "sessionId": sid,
                "allowBlocked": _is_blocked(allow),
                "denyBlocked": _is_blocked(deny),
                "outputType": type(out).__name__,
                "wire": (
                    "Agent(..., tool_input_guardrails=[relay.openai_tool_input(...)], "
                    "tool_output_guardrails=[relay.openai_tool_output(...)])"
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
