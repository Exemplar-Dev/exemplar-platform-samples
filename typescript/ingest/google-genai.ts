/**
 * Session ingest — Google GenAI.
 *
 *   npm run build && npx tsx examples/ingest/google-genai.ts
 */
import { ingestGoogleGenAIGenerateContent } from "@exemplar-dev/exemplar-harness-typescript-sdk";
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const sessionId = newSessionId("ingest-google-genai");
  banner("Ingest + Google GenAI", sessionId);

  const h = harness("google-genai-bot");

  await ingestGoogleGenAIGenerateContent(h, {
    sessionId,
    prompt: "Hello Gemini",
    response: {
      text: "Hello! How can I help you today?",
      usageMetadata: {
        promptTokenCount: 6,
        candidatesTokenCount: 10,
      },
    },
    model: "gemini-2.0-flash",
    sourceApp: SOURCE_APP,
  });
  console.log("Ingested Google GenAI generateContent-shaped response.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
