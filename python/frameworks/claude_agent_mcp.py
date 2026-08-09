"""Live Claude Agent SDK + Exemplar MCP — docs: https://docs.exemplar.dev/tools-mcp/frameworks"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import harness, session_id  # noqa: E402


async def main() -> None:
    h = harness("claude-agent-mcp-sample")
    sid = session_id("claude-agent-mcp")
    toolkit = h.tools()
    mcp = toolkit.for_provider("claude_agent")
    print(f"Claude Agent MCP adapter: {toolkit.mcp_url}")
    print(f"sessionId={sid} provider={type(mcp).__name__}")
    print("See SDK examples/live/claude_agent_demo.py for a full query loop.")
    if hasattr(toolkit, "close_adapters"):
        await toolkit.close_adapters()
    print("\nDocs: https://docs.exemplar.dev/tools-mcp/frameworks")


if __name__ == "__main__":
    asyncio.run(main())
