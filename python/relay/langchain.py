"""Live Relay + LangChain create_agent wrap_tool_call middleware.

Also see langchain_middleware.py for a lighter smoke sample.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import SOURCE_APP, harness, session_id  # noqa: E402


class _Req:
    def __init__(self, name: str, args: dict, call_id: str = "c1") -> None:
        self.tool_call = {"name": name, "args": args, "id": call_id}
        self.tool = None


def main() -> None:
    h = harness("relay-langchain-sample")
    sid = session_id("relay-langchain")
    relay = h.relay(surface="langchain", source_app=SOURCE_APP)
    mw = relay.langchain_middleware(session_id=sid)
    wrap = getattr(mw, "wrap_tool_call", None) or mw

    allow = wrap(_Req("get_weather", {"city": "SF"}), lambda _r: "Sunny in SF")
    deny = wrap(
        _Req("shell", {"command": "rm -rf /tmp/x"}),
        lambda _r: "should-not-run",
    )
    allow_text = getattr(allow, "content", allow)
    deny_text = getattr(deny, "content", deny)

    print(
        json.dumps(
            {
                "example": "relay_langchain",
                "sessionId": sid,
                "middlewareType": type(mw).__name__,
                "allow": str(allow_text),
                "deny": str(deny_text)[:200],
                "wire": "create_agent(..., middleware=[relay.langchain_middleware(...)])",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
