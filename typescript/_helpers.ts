/**
 * Shared helpers for TypeScript live samples.
 * Uses the published @exemplar-dev/exemplar-harness-typescript-sdk package.
 */
import { randomUUID } from "node:crypto";
import { config as loadEnv } from "dotenv";
import { Harness } from "@exemplar-dev/exemplar-harness-typescript-sdk";

loadEnv();

export const SOURCE_APP = "exemplar-platform-samples";

export function requireApiKey(): void {
  if (!process.env.EXEMPLAR_API_KEY?.trim()) {
    console.error(
      "Set EXEMPLAR_API_KEY (org key eis_…) before running samples.\n" +
        "  cp .env.example .env\n" +
        "Docs: https://docs.exemplar.dev/account-settings/tokens-and-api-keys",
    );
    process.exit(1);
  }
}

export function newSessionId(prefix: string): string {
  return `${prefix}-${randomUUID().slice(0, 12)}`;
}

export function harness(agentId = "ts-platform-sample"): Harness {
  requireApiKey();
  return Harness.fromEnv({ agentId });
}

export function banner(title: string, sessionId: string): void {
  console.log(`\n=== ${title} ===`);
  console.log(`sessionId=${sessionId}`);
  console.log("Docs: https://docs.exemplar.dev/marshal/sdk/live-examples");
}
