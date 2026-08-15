import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from trading_agent.agent import root_agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

async def main():
    print("Agent tools:")
    for t in root_agent.tools:
        if isinstance(t, McpToolset):
            print("Found McpToolset. Initializing session...")
            try:
                session = await t._mcp_session_manager.create_session(t._connection_params)
                await session.initialize()
                tools = await session.list_tools()
                print(f"Tools from MCP server: {len(tools.tools)}")
                for mcp_tool in tools.tools:
                     print(f" - {mcp_tool.name}")
            except Exception as e:
                print(f"Error fetching MCP tools: {e}")

if __name__ == "__main__":
    asyncio.run(main())
