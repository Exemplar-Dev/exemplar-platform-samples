# exemplar-platform-samples

**Live** (not simulated) samples for Exemplar Platform — Python and TypeScript Marshal SDKs in one place.

Docs catalog: [docs.exemplar.dev/marshal/sdk/live-examples](https://docs.exemplar.dev/marshal/sdk/live-examples)

| Path | SDK |
|------|-----|
| [`python/`](python/) | [`exemplar-harness-sdk`](https://pypi.org/project/exemplar-harness-sdk/) |
| [`typescript/`](typescript/) | [`@exemplar-dev/exemplar-harness-typescript-sdk`](https://www.npmjs.com/package/@exemplar-dev/exemplar-harness-typescript-sdk) |

These samples call the **live** Exemplar API. You need an org API key (`eis_*`) from [Tokens](https://docs.exemplar.dev/account-settings/tokens-and-api-keys).

## Quick start

### Python

```bash
cd python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set EXEMPLAR_API_KEY

python -m platform.memory
python -m platform.skills
python -m platform.prompts
python -m platform.hitl
python -m relay.evaluate
```

Framework + MCP (extra deps):

```bash
pip install -r requirements-frameworks.txt
# also set GOOGLE_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY as needed
python -m frameworks.langchain_mcp
python -m frameworks.agno_mcp
```

### TypeScript

```bash
cd typescript
npm install
cp .env.example .env   # set EXEMPLAR_API_KEY

npx tsx relay/evaluate.ts
npx tsx ingest/openai.ts
npx tsx relay/openai-agents.ts
```

## Catalog

| Area | Python | TypeScript | Docs |
|------|--------|------------|------|
| Memory | `platform/memory.py` | — | [Memory](https://docs.exemplar.dev/marshal/memory) |
| Skills | `platform/skills.py` | — | [Skills](https://docs.exemplar.dev/marshal/skill-management) |
| Prompts | `platform/prompts.py` | — | [Prompts](https://docs.exemplar.dev/marshal/prompt-management) |
| HITL | `platform/hitl.py` | — | [HITL](https://docs.exemplar.dev/marshal/hitl) |
| LangChain + MCP | `frameworks/langchain_mcp.py` | `ingest/langchain.ts` | [Frameworks](https://docs.exemplar.dev/tools-mcp/frameworks) |
| Agno + MCP | `frameworks/agno_mcp.py` | — | same |
| Google ADK + MCP | `frameworks/google_adk_mcp.py` | — | same |
| Claude Agent + MCP | `frameworks/claude_agent_mcp.py` | `ingest/claude-agent.ts` | same |
| Relay evaluate | `relay/evaluate.py` | `relay/evaluate.ts` | [SDK Relay](https://docs.exemplar.dev/marshal/sdk/client-usage) |
| Relay Agno / LangChain / Claude | `relay/*.py` | `relay/*.ts` | same |
| Session ingest | — | `ingest/*.ts` | [Live examples](https://docs.exemplar.dev/marshal/sdk/live-examples) |

Maintainer copies of the full SDK example matrices still live under each SDK repo (`examples/live`, `examples/relay`, `examples/ingest`). This repo is the **customer-facing** samples home linked from docs and exemplar-skills.

## Related

- [Marshal SDK docs](https://docs.exemplar.dev/marshal/sdk)
- [SDKs & CLI guide](https://docs.exemplar.dev/guides/sdks-and-cli)
- [exemplar-skills](https://github.com/Exemplar-Dev/exemplar-skills) (`/exemplar-harness`)
- [exemplar-harness-sdk](https://github.com/Exemplar-Dev/exemplar-harness-sdk)
- [exemplar-harness-typescript-sdk](https://github.com/Exemplar-Dev/exemplar-harness-typescript-sdk)

## License

Proprietary — Exemplar Dev LLC. Samples are provided for customers integrating with Exemplar Platform.
