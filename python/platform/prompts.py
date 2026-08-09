"""Live prompts registry — docs: https://docs.exemplar.dev/marshal/prompt-management"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import harness  # noqa: E402

SYSTEM = "You are a concise support agent. Answer in one sentence."
USER = "Summarize our refund policy for topic: {{topic}}."
MODEL = "openai/gpt-4o-mini"


def main() -> None:
    h = harness("prompts-sample")
    prompts = h.prompts()
    name = f"sample-support-{uuid.uuid4().hex[:8]}"

    created = prompts.create(
        name=name,
        title="Support summary",
        description="Platform samples demo prompt",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER},
        ],
        variables=["topic"],
        tags=["demo", "samples"],
        default_model=MODEL,
    )
    built = prompts.build(created.prompt_id, variables={"topic": "returns"})
    run_result = prompts.run(
        created.prompt_id,
        variables={"topic": "returns"},
        model=MODEL,
    )
    prompts.delete(created.prompt_id)

    print(
        json.dumps(
            {
                "example": "prompts",
                "promptId": created.prompt_id,
                "name": created.name,
                "buildPreview": next(
                    (m["content"] for m in built.messages if m["role"] == "user"),
                    "",
                )[:200],
                "runPreview": str(run_result.get("content", run_result))[:200],
            },
            indent=2,
        )
    )
    print("\nDocs: https://docs.exemplar.dev/marshal/prompt-management")


if __name__ == "__main__":
    main()
