"""Live Relay evaluate (hook-free) — docs: https://docs.exemplar.dev/marshal/sdk/live-examples"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exemplar_harness.relay import RelayDecision

from common import SOURCE_APP, harness, session_id  # noqa: E402


def main() -> None:
    h = harness("relay-evaluate-sample")
    sid = session_id("relay-evaluate")
    relay = h.relay(surface="openai_agents", source_app=SOURCE_APP)

    verdict = relay.evaluate(
        tool_name="shell",
        arguments={"command": "ls -la"},
        session_id=sid,
        user_id="sample-user",
    )
    bash = relay.evaluate_bash(
        command="rm -rf /tmp/example-relay-probe",
        session_id=sid,
        user_id="sample-user",
    )
    path = relay.evaluate_path(path=".env", session_id=sid)

    print(
        json.dumps(
            {
                "example": "relay_evaluate",
                "sessionId": sid,
                "evaluate": {
                    "decision": str(verdict.decision),
                    "reason": verdict.reason,
                },
                "evaluateBash": {
                    "decision": str(bash.decision),
                    "reason": bash.reason,
                },
                "evaluatePath": {
                    "decision": str(path.decision),
                    "reason": path.reason,
                },
                "deniedShell": verdict.decision is RelayDecision.DENY
                or bash.decision is RelayDecision.DENY,
            },
            indent=2,
        )
    )
    print("\nDocs: https://docs.exemplar.dev/marshal/sdk/client-usage")
    print("IDE hooks still use Relay → Connect / exemplar-skills — not this adapter.")


if __name__ == "__main__":
    main()
