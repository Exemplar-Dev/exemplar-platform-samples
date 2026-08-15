import importlib.util
import os
import shutil
import sys


def _resolve_mcp_command() -> str:
    """Resolve the Python executable that should launch the MCP server."""
    env = os.getenv("MCP_VENV_PY")
    if env:
        return env
    return sys.executable


def _resolve_mcp_server() -> str:
    """Resolve the path to the tradingview_mcp server.py module."""
    env = os.getenv("MCP_SERVER_PATH")
    if env:
        return env
    spec = importlib.util.find_spec("tradingview_mcp.server")
    if spec and spec.origin:
        return spec.origin
    raise RuntimeError(
        "Cannot find tradingview_mcp.server. "
        "Install it: pip install tradingview-mcp-server"
    )


MCP_VENV_PY = _resolve_mcp_command()
MCP_SERVER = _resolve_mcp_server()

GLM_MODEL = os.getenv(
    "GLM_MODEL",
    "ollama_chat/glm-5.2:cloud"
)

DEFAULT_TIMEOUT = int(os.getenv("MCP_TIMEOUT", "30"))
CLI_OUTPUT_LIMIT = 1500

