import os

MCP_VENV_PY = os.getenv(
    "MCP_VENV_PY",
    r"D:\tradingview-mcp\.venv\Scripts\python.exe"
)

MCP_SERVER = os.getenv(
    "MCP_SERVER_PATH",
    r"D:\tradingview-mcp\src\tradingview_mcp\server.py"
)

GLM_MODEL = os.getenv(
    "GLM_MODEL",
    "ollama_chat/glm-5.2:cloud"
)

DEFAULT_TIMEOUT = int(os.getenv("MCP_TIMEOUT", "30"))
CLI_OUTPUT_LIMIT = 1500
