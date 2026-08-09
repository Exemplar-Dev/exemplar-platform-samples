# Relay samples (Python)

In-process Relay adapters for agent frameworks. These call the **live** Exemplar API (`EXEMPLAR_API_KEY`).

IDE hooks (Cursor / Claude / Codex / OpenCode) still use [Relay Connect](https://docs.exemplar.dev/relay/connect) / [exemplar-skills](https://docs.exemplar.dev/guides/ide-agent-skills) — not these adapters.

```bash
cd python
pip install -r requirements.txt
# optional extras for framework packages:
pip install "exemplar-harness-sdk[langchain,agno,google-adk,claude-agent,pydantic-ai,crewai,semantic-kernel]"
cp .env.example .env   # set EXEMPLAR_API_KEY

python -m relay.evaluate
python -m relay.langchain
python -m relay.langgraph
python -m relay.agno
python -m relay.adk
python -m relay.claude_sdk
python -m relay.openai_agents
python -m relay.pydantic_ai
python -m relay.crewai
python -m relay.semantic_kernel
```

| Surface | File | Helper |
|---------|------|--------|
| Hook-free | [`evaluate.py`](evaluate.py) | `evaluate` / `evaluate_bash` / `evaluate_path` |
| LangChain | [`langchain.py`](langchain.py) | `langchain_middleware` |
| LangGraph | [`langgraph.py`](langgraph.py) | `langgraph_middleware` |
| Agno | [`agno.py`](agno.py) | `agno_tool_hook` |
| Google ADK | [`adk.py`](adk.py) | `adk_before_tool` / `adk_after_tool` |
| Claude Agent SDK | [`claude_sdk.py`](claude_sdk.py) | `claude_hooks` |
| OpenAI Agents | [`openai_agents.py`](openai_agents.py) | `openai_tool_input` / `openai_tool_output` |
| Pydantic AI | [`pydantic_ai.py`](pydantic_ai.py) | `pydantic_ai_hooks` |
| CrewAI | [`crewai.py`](crewai.py) | `crewai_hooks` |
| Semantic Kernel | [`semantic_kernel.py`](semantic_kernel.py) | `semantic_kernel_filter` |

TypeScript counterparts: [`../../typescript/relay/`](../../typescript/relay/).

Catalog: [Live SDK examples](https://docs.exemplar.dev/marshal/sdk/live-examples)
