/**
 * Session ingest — Anthropic Messages API.
 *
 * Peers: npm i @anthropic-ai/sdk
 *   npm run build && npx tsx examples/ingest/anthropic.ts
 */
import { HarnessAnthropicSession } from "@exemplar-dev/exemplar-harness-typescript-sdk";
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const sessionId = newSessionId("ingest-anthropic");
  banner("Ingest + Anthropic SDK", sessionId);

  const h = harness("anthropic-ingest-bot");
  const session = new HarnessAnthropicSession(h, {
    sessionId,
    sourceApp: SOURCE_APP,
  });

  const messages = [{ role: "user" as const, content: "Hello" }];
  const response = {
    id: "msg_example",
    model: "claude-sonnet-4-6",
    role: "assistant",
    content: [{ type: "text", text: "Hello! How can I help?" }],
    usage: { input_tokens: 8, output_tokens: 10 },
  };

  await session.onCompletion({ messages, response });
  console.log("Ingested Anthropic message turn.");

  console.log(`
Live:

  import Anthropic from "@anthropic-ai/sdk";

  const client = new Anthropic();
  const response = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 1024,
    messages,
  });
  await session.onCompletion({ messages, response });
`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
