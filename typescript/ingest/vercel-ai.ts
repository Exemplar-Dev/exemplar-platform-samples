/**
 * Session ingest — Vercel AI SDK.
 *
 * Peers: npm i ai
 *   npm run build && npx tsx examples/ingest/vercel-ai.ts
 */
import { ExemplarVercelAISession } from "@exemplar-dev/exemplar-harness-typescript-sdk";
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const sessionId = newSessionId("ingest-vercel-ai");
  banner("Ingest + Vercel AI SDK", sessionId);

  const h = harness("vercel-ai-bot");
  const session = new ExemplarVercelAISession(h, {
    sessionId,
    sourceApp: SOURCE_APP,
    modelId: "gpt-4o-mini",
  });

  const prompt = "Summarize our refund policy in one sentence.";
  await session.ingestTurn(prompt, {
    text: "Returns are accepted within 30 days of purchase.",
    usage: { promptTokens: 24, completionTokens: 12 },
    response: { modelId: "gpt-4o-mini" },
  });
  console.log("Ingested one Vercel AI finish turn.");

  console.log(`
Live generateText:

  import { generateText } from "ai";

  await generateText({
    model: yourModel,
    prompt,
    onFinish: session.onFinish(prompt),
  });
`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
