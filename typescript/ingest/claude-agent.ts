/**
 * Session ingest — Claude Agent SDK query stream.
 *
 * Peers: npm i @anthropic-ai/claude-agent-sdk
 *   npm run build && npx tsx examples/ingest/claude-agent.ts
 */
import { ingestClaudeAgentResult } from "@exemplar-dev/exemplar-harness-typescript-sdk";
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const sessionId = newSessionId("ingest-claude-agent");
  banner("Ingest + Claude Agent SDK", sessionId);

  const h = harness("claude-agent-ingest-bot");
  const prompt = "Summarize README.md";

  await ingestClaudeAgentResult(h, {
    sessionId,
    prompt,
    result: {
      type: "result",
      result: "README describes the Exemplar harness TypeScript SDK.",
      subtype: "success",
    },
    sourceApp: SOURCE_APP,
  });
  console.log("Ingested Claude Agent result-shaped message.");

  console.log(`
Live:

  import { query } from "@anthropic-ai/claude-agent-sdk";
  import { ingestClaudeAgentQuery } from "@exemplar-dev/exemplar-harness-typescript-sdk";

  await ingestClaudeAgentQuery(h, {
    sessionId,
    prompt,
    messages: query({ prompt }),
    sourceApp: "${SOURCE_APP}",
  });
`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
