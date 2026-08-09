/**
 * Relay + OpenAI Agents SDK (`surface: "openai_agents"`).
 *
 * Peers: npm i @openai/agents openai
 * Env:   EXEMPLAR_API_KEY, OPENAI_API_KEY (for a live agent run)
 *
 *   npm run build && npx tsx examples/relay/openai-agents.ts
 *
 * Without OPENAI_API_KEY this still exercises decide/observe via the guardrails
 * against a mocked tool call shape.
 */
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const h = harness("openai-agents-relay-bot");
  const sessionId = newSessionId("relay-openai-agents");
  banner("Relay + OpenAI Agents", sessionId);
  const relay = h.relay({
    surface: "openai_agents",
    sourceApp: SOURCE_APP,
  });

  const inputGuard = relay.openaiToolInput(sessionId);
  const outputGuard = relay.openaiToolOutput(sessionId);

  // Dry-run the guardrail against a tool-call shaped payload (no Agents peer required).
  const dry = await inputGuard({
    tool_name: "shell",
    tool_arguments: { command: "echo hello" },
  });
  console.log("openaiToolInput (dry):", dry);

  await outputGuard({
    tool_name: "shell",
    tool_arguments: { command: "echo hello" },
    output: "hello",
  });
  console.log("openaiToolOutput (dry): observed");

  if (!process.env.OPENAI_API_KEY?.trim()) {
    console.log(
      "\nSkipping live Agent run (set OPENAI_API_KEY + install @openai/agents to enable).",
    );
    console.log("Wire-up sketch:");
    console.log(`
  import { Agent, run, tool } from "@openai/agents";

  const lookup = tool({
    name: "lookup_order",
    description: "Look up an order by id",
    parameters: { type: "object", properties: { orderId: { type: "string" } }, required: ["orderId"] },
    execute: async ({ orderId }) => ({ orderId, status: "shipped" }),
  });

  const agent = new Agent({
    name: "Support",
    instructions: "Use tools when needed.",
    tools: [lookup],
    // Attach Relay decide/observe:
    // toolInputGuardrails: [inputGuard],
    // toolOutputGuardrails: [outputGuard],
  });

  await run(agent, "What is the status of order ORD-1?");
`);
    return;
  }

  try {
    const agents = await import("@openai/agents");
    const lookup = agents.tool({
      name: "lookup_order",
      description: "Look up an order by id",
      parameters: {
        type: "object",
        properties: { orderId: { type: "string" } },
        required: ["orderId"],
        additionalProperties: false,
      },
      strict: true,
      execute: async (input: { orderId: string }) => ({
        orderId: input.orderId,
        status: "shipped",
      }),
    });

    const agent = new agents.Agent({
      name: "Support",
      instructions: "Use lookup_order when the user asks about an order.",
      tools: [lookup],
    });

    // Prefer SDK-native guardrail helpers when present; otherwise rely on decide via dry path above.
    console.log("Running agent (Relay decide still available via openaiToolInput/Output)…");
    const result = await agents.run(agent, "Status of order ORD-42?");
    console.log("agent output:", String((result as { finalOutput?: unknown }).finalOutput ?? result));
  } catch (err) {
    console.warn("Live Agents run skipped:", err instanceof Error ? err.message : err);
    console.warn("Install peers: npm i @openai/agents openai");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
