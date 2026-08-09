"""Live skills registry — docs: https://docs.exemplar.dev/marshal/skill-management"""

from __future__ import annotations

import json
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import harness  # noqa: E402

INSTRUCTIONS = """# Refund policy helper

1. Confirm order date.
2. Check return window (30 days).
3. Offer store credit or refund.
"""


def main() -> None:
    h = harness("skills-sample")
    skills = h.skills()
    name = f"sample-refund-{uuid.uuid4().hex[:8]}"

    created = skills.create(
        name=name,
        instructions=INSTRUCTIONS,
        description="Platform samples demo skill",
        tags=["demo", "samples"],
        files={"references/policy.md": "# Policy\n\n30-day returns.\n"},
    )
    listed = skills.list(limit=20)
    fetched = skills.get(name)
    search = skills.search("refund", top_k=5)

    with tempfile.TemporaryDirectory(prefix="exemplar-skills-") as tmp:
        installed = skills.install(Path(tmp) / "skills", names=[name])

    skills.delete(created.skill_id)

    print(
        json.dumps(
            {
                "example": "skills",
                "skillId": created.skill_id,
                "name": created.name,
                "listCount": len(listed),
                "instructionsPreview": fetched.instructions[:80],
                "searchCount": len(search),
                "installed": [p.name for p in installed],
            },
            indent=2,
        )
    )
    print("\nDocs: https://docs.exemplar.dev/marshal/skill-management")


if __name__ == "__main__":
    main()
