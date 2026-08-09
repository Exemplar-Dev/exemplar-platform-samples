/**
 * Session ingest — OpenAI chat completions.
 *
 * Peers: npm i openai
 *   npm run build && npx tsx examples/ingest/openai.ts
 */
import { ingestOpenAIChatCompletion } from "@exemplar-dev/exemplar-harness-typescript-sdk";
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const sessionId = newSessionId("ingest-openai");
  banner("Ingest + OpenAI SDK", sessionId);

  const h = harness("openai-ingest-bot");
  const prompt = "Hello!";

  // Shape-compatible stub (no network) so the example always runs.
  const response = {
    id: "chatcmpl-example",
    model: "gpt-4o-mini",
    choices: [
      {
        index: 0,
        message: { role: "assistant", content: "Hi! How can I help?" },
        finish_reason: "stop",
      },
    ],
    usage: { prompt_tokens: 8, completion_tokens: 6, total_tokens: 14 },
  };

  await ingestOpenAIChatCompletion(h, {
    sessionId,
    userPrompt: prompt,
    response,
    sourceApp: SOURCE_APP,
  });
  console.log("Ingested OpenAI chat completion turn.");

  if (process.env.OPENAI_API_KEY?.trim()) {
    try {
      const OpenAI = (await import("openai")).default;
      const client = new OpenAI();
      const livePrompt = "Say hello in one short sentence.";
      const live = await client.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: livePrompt }],
      });
      await ingestOpenAIChatCompletion(h, {
        sessionId,
        userPrompt: livePrompt,
        response: live,
        sourceApp: SOURCE_APP,
      });
      console.log("Ingested live OpenAI completion.");
    } catch (err) {
      console.warn("Live OpenAI call skipped:", err instanceof Error ? err.message : err);
    }
  } else {
    console.log("Set OPENAI_API_KEY to also run a live completion.");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
