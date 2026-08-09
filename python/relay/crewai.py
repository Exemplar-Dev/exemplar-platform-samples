"""Live Relay + CrewAI before/after tool-call hooks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import SOURCE_APP, harness, session_id  # noqa: E402


class _Ctx:
    def __init__(self, tool_name: str, tool_input: dict, tool_result: object = None) -> None:
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.tool_result = tool_result


def main() -> None:
    h = harness("relay-crewai-sample")
    sid = session_id("relay-crewai")
    relay = h.relay(surface="crewai", source_app=SOURCE_APP)
    before, after = relay.crewai_hooks(session_id=sid)

    allow = before(_Ctx("get_weather", {"city": "SF"}))
    deny = before(_Ctx("shell", {"command": "rm -rf /tmp/x"}))
    after(_Ctx("get_weather", {"city": "SF"}, tool_result="Sunny"))

    print(
        json.dumps(
            {
                "example": "relay_crewai",
                "sessionId": sid,
                "beforeAllow": allow,
                "beforeDeny": deny,
                "wire": "relay.crewai_register(session_id=...) or before_tool_call / after_tool_call",
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
