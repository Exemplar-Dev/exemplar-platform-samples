/**
 * Relay + LangChain.js / LangGraph.js (`surface: "langchain"` | `"langgraph"`).
 *
 * Peers: npm i langchain @langchain/core
 * Env:   EXEMPLAR_API_KEY (+ model keys for a live createAgent run)
 *
 *   npm run build && npx tsx examples/relay/langchain.ts
 */
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const h = harness("langchain-relay-bot");
  const sessionId = newSessionId("relay-langchain");
  banner("Relay + LangChain.js", sessionId);

  const relay = h.relay({
    surface: "langchain",
    sourceApp: SOURCE_APP,
  });

  const mwConfig = relay.langchainMiddleware(sessionId);
  console.log("middleware name:", mwConfig.name);

  let handlerRan = false;
  const result = await mwConfig.wrapToolCall(
    {
      toolCall: {
        name: "shell",
        args: { command: "cat /etc/passwd" },
        id: "call_example",
      },
    },
    async () => {
      handlerRan = true;
      return { ok: true };
    },
  );
  console.log("wrapToolCall result:", result);
  console.log(
    handlerRan
      ? "handler ran (policy allowed or fail-open on transport error)"
      : "handler skipped (Relay denied / asked)",
  );

  // Second call: benign tool — observe path when allowed.
  handlerRan = false;
  const allowed = await mwConfig.wrapToolCall(
    {
      toolCall: {
        name: "lookup_order",
        args: { orderId: "ORD-1" },
        id: "call_ok",
      },
    },
    async () => {
      handlerRan = true;
      return { orderId: "ORD-1", status: "shipped" };
    },
  );
  console.log("lookup_order:", { allowed, handlerRan });

  console.log(`
Wire into LangChain createAgent:

  import { createAgent, createMiddleware } from "langchain";

  const middleware = createMiddleware(relay.langchainMiddleware(sessionId));
  // langgraph surface: relay.langgraphMiddleware(sessionId) — same shape

  const agent = createAgent({
    model: yourModel,
    tools: [/* … */],
    middleware: [middleware],
  });

  await agent.invoke({ messages: [{ role: "user", content: "Check order ORD-1" }] });
`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
