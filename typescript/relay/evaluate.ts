/**
 * Hook-free Relay evaluate / verdict (no framework peers required).
 *
 *   export EXEMPLAR_API_KEY=eis_…
 *   npm run build && npx tsx examples/relay/evaluate.ts
 */
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const h = harness("relay-evaluate-bot");
  const sessionId = newSessionId("relay-evaluate");
  banner("Relay evaluate (hook-free)", sessionId);
  const relay = h.relay({
    surface: "openai_agents",
    sourceApp: SOURCE_APP,
  });

  const [decision, reason] = await relay.verdict({
    sessionId,
    toolName: "shell",
    arguments: { command: "ls -la" },
  });
  console.log("verdict:", { decision, reason: reason || "(none)" });

  const bash = await relay.evaluateBash({
    command: "rm -rf /tmp/example-relay-probe",
    sessionId,
    userId: "example-user",
  });
  console.log("evaluateBash:", {
    decision: bash.decision,
    reason: bash.reason || "(none)",
    resourceKind: bash.resourceKind,
  });

  const pathVerdict = await relay.evaluatePath({
    path: ".env",
    sessionId,
  });
  console.log("evaluatePath(.env):", {
    decision: pathVerdict.decision,
    reason: pathVerdict.reason || "(none)",
  });

  console.log("\nDone. Check Relay audit / Control rules in the Exemplar console.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
