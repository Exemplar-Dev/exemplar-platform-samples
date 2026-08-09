"""Live memory CRUD — docs: https://docs.exemplar.dev/marshal/memory"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import harness, session_id  # noqa: E402

APP_ID = "platform-samples-memory"


def main() -> None:
    h = harness("memory-sample")
    user_id = "sample-user"
    sid = session_id("memory")
    memory = h.memory(user_id=user_id, session_id=sid, app_id=APP_ID)

    added = memory.add(
        "The user's favorite color is blue.",
        memory_type="fact",
        metadata={"demo": True},
    )
    memory_id = str(added.get("memoryId") or "")
    memory.add("User works in engineering.", memory_type="fact", metadata={"demo": True})

    listed = memory.list(limit=10)
    fetched = memory.get(memory_id)
    search = memory.search("favorite color", top_k=5, search_mode="hybrid")
    recall = memory.recall("What is my favorite color?", format="markdown")
    updated = memory.update(memory_id, content="The user's favorite color is navy blue.")
    deleted = memory.delete_bulk(memory_type="fact")

    print(
        json.dumps(
            {
                "example": "memory",
                "sessionId": sid,
                "memoryId": memory_id,
                "listCount": len(listed),
                "getContent": fetched.content,
                "searchTop": search[0].content if search else None,
                "recallPreview": (recall or "")[:200],
                "updatedContent": updated.content,
                "deletedBulkCount": deleted,
            },
            indent=2,
        )
    )
    print("\nDocs: https://docs.exemplar.dev/marshal/memory")
    print("Catalog: https://docs.exemplar.dev/marshal/sdk/live-examples")


if __name__ == "__main__":
    main()
