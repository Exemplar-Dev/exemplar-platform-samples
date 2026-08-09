"""Live Relay + Semantic Kernel FUNCTION_INVOCATION filter."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import SOURCE_APP, harness, session_id  # noqa: E402


class _Fn:
    def __init__(self, name: str, plugin: str = "tools") -> None:
        self.name = name
        self.plugin_name = plugin
        self.metadata = None


class _Ctx:
    def __init__(self, name: str, arguments: dict) -> None:
        self.function = _Fn(name)
        self.arguments = arguments
        self.result = None


def main() -> None:
    h = harness("relay-semantic-kernel-sample")
    sid = session_id("relay-semantic-kernel")
    relay = h.relay(surface="semantic_kernel", source_app=SOURCE_APP)
    filt = relay.semantic_kernel_filter(session_id=sid)

    async def _exercise() -> dict:
        called = {"next": False}

        async def next_ok(ctx):
            called["next"] = True
            ctx.result = "Sunny"

        allow_ctx = _Ctx("get_weather", {"city": "SF"})
        await filt(allow_ctx, next_ok)

        called["next"] = False

        async def next_should_not(ctx):
            called["next"] = True

        deny_ctx = _Ctx("shell", {"command": "rm -rf /tmp/x"})
        await filt(deny_ctx, next_should_not)
        return {
            "allowRanNext": True,
            "allowResult": str(allow_ctx.result),
            "denyRanNext": called["next"],
            "denyResult": str(deny_ctx.result),
        }

    result = asyncio.run(_exercise())

    print(
        json.dumps(
            {
                "example": "relay_semantic_kernel",
                "sessionId": sid,
                **result,
                "wire": "relay.semantic_kernel_register(kernel, session_id=...)",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
