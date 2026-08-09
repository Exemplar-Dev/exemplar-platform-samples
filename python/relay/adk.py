"""Live Relay + Google ADK before/after tool callbacks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import SOURCE_APP, harness, session_id  # noqa: E402


class _Tool:
    def __init__(self, name: str) -> None:
        self.name = name


def main() -> None:
    h = harness("relay-adk-sample")
    sid = session_id("relay-adk")
    relay = h.relay(surface="adk", source_app=SOURCE_APP)
    before = relay.adk_before_tool(session_id=sid)
    after = relay.adk_after_tool(session_id=sid)

    allow = before(_Tool("get_weather"), {"city": "SF"})
    deny = before(_Tool("shell"), {"command": "rm -rf /tmp/x"})
    after(_Tool("get_weather"), {"city": "SF"}, tool_response="Sunny")

    print(
        json.dumps(
            {
                "example": "relay_adk",
                "sessionId": sid,
                "beforeAllow": allow,
                "beforeDeny": deny,
                "wire": (
                    "LlmAgent(..., before_tool_callback=relay.adk_before_tool(...), "
                    "after_tool_callback=relay.adk_after_tool(...))"
                ),
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
