"""Live Google ADK + Exemplar MCP — docs: https://docs.exemplar.dev/tools-mcp/frameworks"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import harness, session_id  # noqa: E402


async def main() -> None:
    h = harness("adk-mcp-sample")
    sid = session_id("adk-mcp")
    toolkit = h.tools()
    mcp = toolkit.for_provider("google_adk")
    toolset = await mcp.get_tools() if hasattr(mcp, "get_tools") else mcp
    print(f"Google ADK MCP ready: {toolkit.mcp_url}")
    print(f"sessionId={sid} toolset={type(toolset).__name__}")
    print("Wire toolset into your ADK agent; see SDK live google_adk_demo for a full loop.")
    if hasattr(toolkit, "close_adapters"):
        await toolkit.close_adapters()
    print("\nDocs: https://docs.exemplar.dev/tools-mcp/frameworks")


if __name__ == "__main__":
    asyncio.run(main())
