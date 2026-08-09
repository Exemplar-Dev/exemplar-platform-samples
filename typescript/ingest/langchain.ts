/**
 * Session ingest — LangChain.js / LangGraph.js callbacks.
 *
 *   npm run build && npx tsx examples/ingest/langchain.ts
 */
import {
  HarnessLangChainHandler,
  HarnessLangGraphHandler,
} from "@exemplar-dev/exemplar-harness-typescript-sdk";
import { harness, newSessionId, banner, SOURCE_APP } from "../_helpers.ts";

async function main(): Promise<void> {
  const sessionId = newSessionId("ingest-langchain");
  banner("Ingest + LangChain.js", sessionId);

  const h = harness("langchain-ingest-bot");
  const handler = new HarnessLangChainHandler(h, {
    sessionId,
    sourceApp: SOURCE_APP,
    model: "gpt-4o-mini",
  });

  handler.setUserInput("Refund policy?");
  await handler.handleLLMEnd({
    generations: [[{ text: "Returns are accepted within 30 days." }]],
    llmOutput: {
      model_name: "gpt-4o-mini",
      tokenUsage: { promptTokens: 20, completionTokens: 10 },
    },
  });

  console.log("Ingested LangChain llm_end turn.");
  console.log(`LangGraph handler: ${HarnessLangGraphHandler.name}`);
  console.log(`
Live:

  await chain.invoke(input, { callbacks: [handler] });
  await graph.invoke(state, {
    callbacks: [new HarnessLangGraphHandler(h, { sessionId, sourceApp: "${SOURCE_APP}" })],
  });
`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
