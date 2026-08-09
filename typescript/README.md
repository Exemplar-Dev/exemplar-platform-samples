# TypeScript samples

Uses the published [`@exemplar-dev/exemplar-harness-typescript-sdk`](https://www.npmjs.com/package/@exemplar-dev/exemplar-harness-typescript-sdk).

```bash
npm install
cp .env.example .env   # EXEMPLAR_API_KEY=eis_…

npx tsx relay/evaluate.ts
npx tsx ingest/openai.ts
npm run relay:openai-agents
```

Optional peer packages (openai, @openai/agents, ai, etc.) enable live provider calls inside ingest samples; stub ingest always works with only `EXEMPLAR_API_KEY`.

Docs: https://docs.exemplar.dev/marshal/sdk/live-examples
