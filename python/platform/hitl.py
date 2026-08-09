"""Live HITL approvals — docs: https://docs.exemplar.dev/marshal/hitl

Demo-only: a background thread self-approves with the same org key so the
sample finishes without a human. Production agents must not self-approve —
use the console HITL inbox or separate reviewer credentials.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from common import harness  # noqa: E402

AGENT_ID = "hitl-sample"


def _respond_later(h, request_id: str, delay: float = 2.0, **body) -> None:
    def _post() -> None:
        time.sleep(delay)
        resp = httpx.post(
            f"{h._base_url.rstrip('/')}/api/harness-hitl/v1/requests/{request_id}/respond",
            json=body,
            headers={
                "Authorization": f"Bearer {h._api_key}",
                "X-API-Key": h._api_key,
            },
            timeout=30.0,
        )
        resp.raise_for_status()

    threading.Thread(target=_post, daemon=True).start()


def main() -> None:
    h = harness(AGENT_ID)
    hitl = h.hitl(agent_id=AGENT_ID)

    approval = hitl.request_approval(
        "Deploy build 1234 to production?",
        description="All checks green. Blast radius: payments service.",
        payload={"build": "1234", "service": "payments"},
        ttl_seconds=900,
    )
    _respond_later(h, approval.request_id, decision="approved", comment="LGTM")
    approval = hitl.wait(approval.request_id, timeout=60, poll_interval=1)

    question = hitl.request_input("Which rollback strategy?", ttl_seconds=900)
    _respond_later(h, question.request_id, text="Blue-green with a 10% canary")
    question = hitl.wait(question.request_id, timeout=60, poll_interval=1)

    choice = hitl.request_select(
        "Pick a deployment region",
        ["us-east-1", "eu-west-1"],
        ttl_seconds=900,
    )
    _respond_later(h, choice.request_id, option="us-east-1")
    choice = hitl.wait(choice.request_id, timeout=60, poll_interval=1)

    rotation = hitl.request_approval("Rotate production credentials?", ttl_seconds=900)
    rotation = hitl.cancel(rotation.request_id)

    print(
        json.dumps(
            {
                "example": "hitl",
                "approval": {
                    "requestId": approval.request_id,
                    "state": getattr(approval, "state", None),
                    "approved": getattr(approval, "approved", None),
                },
                "input": {
                    "requestId": question.request_id,
                    "text": getattr(question, "text", None),
                },
                "select": {
                    "requestId": choice.request_id,
                    "option": getattr(choice, "option", None),
                },
                "cancelled": rotation.request_id,
            },
            indent=2,
            default=str,
        )
    )
    print("\nDocs: https://docs.exemplar.dev/marshal/hitl")
    print("Console: Marshal → HITL Approvals")


if __name__ == "__main__":
    main()
