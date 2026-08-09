/**
 * Session ingest — OpenAI Agents SDK.
 *
 * Peers: npm i @openai/agents openai
 *   npm run build && npx tsx examples/ingest/openai-agents.ts
 */
import { ingestOpenAIAgentsRun } from "@exemplar-dev/exemplar-harness-typescript-sdk";
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const sessionId = newSessionId("ingest-openai-agents");
  banner("Ingest + OpenAI Agents", sessionId);

  const h = harness("openai-agents-ingest-bot");

  await ingestOpenAIAgentsRun(h, {
    sessionId,
    input: "Write a haiku about recursion.",
    result: {
      finalOutput:
        "Functions call themselves—\nlayers deep, then climb back up.\nStack unfolds to truth.",
    },
    sourceApp: SOURCE_APP,
    agentName: "poet",
  });
  console.log("Ingested OpenAI Agents-shaped run.");

  console.log(`
Live wrap:

  import { Agent, run } from "@openai/agents";
  import { wrapOpenAIAgentsRun } from "@exemplar-dev/exemplar-harness-typescript-sdk";

  const traced = wrapOpenAIAgentsRun(h, run, {
    sessionId,
    sourceApp: "${SOURCE_APP}",
  });
  const agent = new Agent({ name: "Assistant", instructions: "Be concise." });
  await traced(agent, "Write a haiku about recursion.");
`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
