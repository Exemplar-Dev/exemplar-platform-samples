/**
 * Relay + Claude Agent SDK (`surface: "claude_sdk"`).
 *
 * Peers: npm i @anthropic-ai/claude-agent-sdk
 * Env:   EXEMPLAR_API_KEY (plus Claude Agent SDK auth per their docs)
 *
 *   npm run build && npx tsx examples/relay/claude-agent.ts
 */
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const h = harness("claude-agent-relay-bot");
  const sessionId = newSessionId("relay-claude-agent");
  banner("Relay + Claude Agent SDK", sessionId);
  const relay = h.relay({
    surface: "claude_sdk",
    sourceApp: SOURCE_APP,
  });

  const hooks = relay.claudeHooks({ sessionId });
  console.log("claudeHooks keys:", Object.keys(hooks));

  const preList = hooks.PreToolUse as Array<{
    hooks?: Array<(...a: unknown[]) => unknown>;
  }>;
  const pre = preList?.[0]?.hooks?.[0];
  if (typeof pre === "function") {
    const decision = await pre({
      tool_name: "Bash",
      tool_input: { command: "pwd" },
      tool_use_id: "toolu_example",
    });
    console.log("PreToolUse decide:", JSON.stringify(decision, null, 2));
  }

  const postList = hooks.PostToolUse as Array<{
    hooks?: Array<(...a: unknown[]) => unknown>;
  }>;
  const post = postList?.[0]?.hooks?.[0];
  if (typeof post === "function") {
    await post({
      tool_name: "Bash",
      tool_input: { command: "pwd" },
      tool_response: "/tmp",
      tool_use_id: "toolu_example",
    });
    console.log("PostToolUse observe: ok");
  }

  console.log(`
Wire into Claude Agent SDK:

  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "List files in the current directory",
    options: { hooks }, // relay.claudeHooks({ sessionId })
  })) {
    console.log(message);
  }
`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
