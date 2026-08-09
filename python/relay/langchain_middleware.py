"""Live Relay + LangChain middleware — attach to a real agent in your app.

Docs: https://docs.exemplar.dev/tools-mcp/frameworks
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import SOURCE_APP, harness, session_id  # noqa: E402


def main() -> None:
    h = harness("relay-langchain-sample")
    sid = session_id("relay-langchain")
    relay = h.relay(surface="langchain", source_app=SOURCE_APP)
    middleware = relay.langchain_middleware(session_id=sid)

    # Smoke the evaluate path the middleware uses
    allow = relay.evaluate(
        tool_name="read",
        arguments={"path": "README.md"},
        session_id=sid,
    )
    deny = relay.evaluate(
        tool_name="shell",
        arguments={"command": "rm -rf /"},
        session_id=sid,
    )

    print(
        json.dumps(
            {
                "example": "relay_langchain",
                "sessionId": sid,
                "middlewareType": type(middleware).__name__,
                "allowRead": str(allow.decision),
                "denyRm": str(deny.decision),
                "wire": "pass middleware into your LangChain / LangGraph agent hooks",
            },
            indent=2,
        )
    )
    print("\nFull agent loop sample: python -m frameworks.langchain_mcp")


if __name__ == "__main__":
    main()
