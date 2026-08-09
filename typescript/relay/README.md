# Relay samples (TypeScript)

In-process Relay adapters. Live API only — set `EXEMPLAR_API_KEY`.

IDE hooks still use [Relay Connect](https://docs.exemplar.dev/relay/connect) / exemplar-skills.

```bash
cd typescript
npm install
cp .env.example .env

npx tsx relay/evaluate.ts
npx tsx relay/langchain.ts
npx tsx relay/openai-agents.ts
npx tsx relay/claude-agent.ts
npx tsx relay/mastra.ts
```

| Surface | File |
|---------|------|
| Hook-free evaluate | [`evaluate.ts`](evaluate.ts) |
| LangChain.js | [`langchain.ts`](langchain.ts) |
| OpenAI Agents | [`openai-agents.ts`](openai-agents.ts) |
| Claude Agent SDK | [`claude-agent.ts`](claude-agent.ts) |
| Mastra | [`mastra.ts`](mastra.ts) |

Python counterparts: [`../../python/relay/`](../../python/relay/).

Catalog: [Live SDK examples](https://docs.exemplar.dev/marshal/sdk/live-examples)
