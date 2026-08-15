import os
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from trading_agent.config import DEFAULT_TIMEOUT, MCP_SERVER, MCP_VENV_PY


def create_mcp_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=MCP_VENV_PY,
                args=[MCP_SERVER],
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            ),
            timeout=DEFAULT_TIMEOUT,
        )
    )
