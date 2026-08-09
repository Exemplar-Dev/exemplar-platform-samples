/**
 * Relay + Mastra (`surface: "mastra"`).
 *
 * Peers: npm i @mastra/core
 * Env:   EXEMPLAR_API_KEY (+ model provider keys for a live generate)
 *
 *   npm run build && npx tsx examples/relay/mastra.ts
 */
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const h = harness("mastra-relay-bot");
  const sessionId = newSessionId("relay-mastra");
  banner("Relay + Mastra", sessionId);
  const relay = h.relay({
    surface: "mastra",
    sourceApp: SOURCE_APP,
  });

  const hooks = relay.mastraHooks(sessionId);

  const blocked = await hooks.beforeToolCall({
    toolName: "shell",
    input: { command: "rm -rf /" },
  });
  console.log("beforeToolCall:", blocked ?? { proceed: true });

  if (!blocked || blocked.proceed !== false) {
    await hooks.afterToolCall({
      toolName: "shell",
      input: { command: "echo ok" },
      output: "ok",
    });
    console.log("afterToolCall: observed");
  }

  console.log(`
Wire into Mastra Agent:

  import { Agent } from "@mastra/core/agent";

  const agent = new Agent({
    name: "support",
    instructions: "Be helpful.",
    model: yourModel,
    tools: { /* … */ },
    hooks, // from relay.mastraHooks(sessionId)
  });

  await agent.generate("Help me check order status");
`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
