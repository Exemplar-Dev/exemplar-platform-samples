"""Live Relay + Agno tool_hooks — docs: https://docs.exemplar.dev/marshal/sdk/live-examples"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exemplar_harness.relay import RelayDenied

from common import SOURCE_APP, harness, session_id  # noqa: E402


def _get_weather(city: str) -> str:
    return f"Sunny in {city}"


def _run_shell(command: str) -> str:
    return f"ran: {command}"


def main() -> None:
    h = harness("relay-agno-sample")
    sid = session_id("relay-agno")
    relay = h.relay(surface="agno", source_app=SOURCE_APP)
    hook = relay.agno_tool_hook(session_id=sid)

    allowed = hook("get_weather", _get_weather, {"city": "SF"})
    denied = False
    deny_reason = None
    try:
        hook("shell", _run_shell, {"command": "rm -rf /tmp/x"})
    except RelayDenied as exc:
        denied = True
        deny_reason = str(exc)

    print(
        json.dumps(
            {
                "example": "relay_agno",
                "sessionId": sid,
                "allowed": allowed,
                "denied": denied,
                "denyReason": deny_reason,
                "wire": "Agent(..., tool_hooks=[relay.agno_tool_hook(session_id=...)])",
            },
            indent=2,
        )
    )
    print("\nDocs: https://docs.exemplar.dev/marshal/sdk/client-usage#relay--policy-decide--observe--evaluate")


if __name__ == "__main__":
    main()
