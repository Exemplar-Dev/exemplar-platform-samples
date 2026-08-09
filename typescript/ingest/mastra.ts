/**
 * Session ingest — Mastra agent.generate.
 *
 *   npm run build && npx tsx examples/ingest/mastra.ts
 */
import { ExemplarMastraSession, ingestMastraGenerate } from "@exemplar-dev/exemplar-harness-typescript-sdk";
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const sessionId = newSessionId("ingest-mastra");
  banner("Ingest + Mastra", sessionId);

  const h = harness("mastra-ingest-bot");

  await ingestMastraGenerate(h, {
    sessionId,
    prompt: "Help me organize my day",
    result: {
      text: "Block focus time at 9am, meetings after lunch.",
      usage: { promptTokens: 18, completionTokens: 14 },
    },
    sourceApp: SOURCE_APP,
    agentName: "planner",
  });
  console.log("Ingested Mastra generate result.");

  const session = new ExemplarMastraSession(h, {
    sessionId,
    sourceApp: SOURCE_APP,
    agentName: "planner",
  });
  console.log(`
Live wrap:

  const generate = session.wrapGenerate(
    (prompt: string) => agent.generate(prompt),
    (prompt) => prompt,
  );
  await generate("Help me organize my day");
  // sessionId=${session.sessionId}
`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
