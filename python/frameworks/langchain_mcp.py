"""Live LangChain + Exemplar MCP tools.

Docs: https://docs.exemplar.dev/tools-mcp/frameworks
Requires: pip install -r requirements-frameworks.txt and GOOGLE_API_KEY (or change LLM).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import SOURCE_APP, harness, session_id  # noqa: E402


async def main() -> None:
    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        print(
            "Set GOOGLE_API_KEY (default demo) or adapt the LLM client.\n"
            "MCP tools still load with EXEMPLAR_API_KEY alone.",
            file=sys.stderr,
        )

    h = harness("langchain-mcp-sample")
    sid = session_id("langchain-mcp")
    toolkit = h.tools()
    mcp = toolkit.for_provider("langchain")
    mcp_tools = await mcp.get_tools()
    print(f"Loaded {len(mcp_tools)} MCP tools from {toolkit.mcp_url}")
    print("sessionId=", sid, "sourceApp=", SOURCE_APP)

    if not os.environ.get("GOOGLE_API_KEY"):
        print("Skipping agent invoke (no GOOGLE_API_KEY). Tools loaded successfully.")
        await toolkit.close_adapters()
        return

    from langchain_core.messages import HumanMessage
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.prebuilt import create_react_agent

    from exemplar_harness.integrations.langchain import make_langchain_callback_handler

    handler = make_langchain_callback_handler(
        h, session_id=sid, chain_name="platform-samples"
    )
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", callbacks=[handler])
    agent = create_react_agent(llm, mcp_tools)
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="List available Exemplar MCP tools briefly.")]},
        config={"callbacks": [handler]},
    )
    print(result["messages"][-1].content)
    await toolkit.close_adapters()
    print("\nDocs: https://docs.exemplar.dev/tools-mcp/frameworks")


if __name__ == "__main__":
    asyncio.run(main())
