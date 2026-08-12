"""Live Agno + Exemplar MCP tools — docs: https://docs.exemplar.dev/tools-mcp/frameworks"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import harness, session_id  # noqa: E402


async def main() -> None:
    h = harness("agno-mcp-sample")
    sid = session_id("agno-mcp")
    toolkit = h.tools()
    mcp = toolkit.for_provider("agno")
    await mcp.connect()
    try:
        print(f"Agno MCP connected: {toolkit.mcp_url} sessionId={sid}")
        if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
            print("Skipping agent run (set GOOGLE_API_KEY or OPENAI_API_KEY). MCP OK.")
            return

        from agno.agent import Agent
        from agno.models.google import Gemini

        from exemplar_harness.integrations.agno import harness_agno_post_hook

        agent = Agent(
            name="platform-samples",
            model=Gemini(id="gemini-2.5-flash"),
            tools=[mcp],
            post_hooks=[
                harness_agno_post_hook(
                    h,
                    session_id=sid,
                    agent_id="agno-mcp-sample",
                    auto_judge_run=True,
                    auto_session_eval=True,
                )
            ],
            instructions=["Use MCP tools when helpful. Be concise."],
        )
        result = await agent.arun("List one Exemplar MCP tool you can see.")
        print(getattr(result, "content", result))
    finally:
        await mcp.close()
    print("\nDocs: https://docs.exemplar.dev/tools-mcp/frameworks")


if __name__ == "__main__":
    asyncio.run(main())
