"""Live Relay + Claude Agent SDK PreToolUse / PostToolUse hooks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import SOURCE_APP, harness, session_id  # noqa: E402


def main() -> None:
    h = harness("relay-claude-sdk-sample")
    sid = session_id("relay-claude-sdk")
    relay = h.relay(surface="claude_sdk", source_app=SOURCE_APP)
    hooks = relay.claude_hooks(session_id=sid)

    pre_entry = hooks["PreToolUse"][0]
    post_entry = hooks["PostToolUse"][0]
    pre_hooks = getattr(pre_entry, "hooks", None) or pre_entry.get("hooks")
    post_hooks = getattr(post_entry, "hooks", None) or post_entry.get("hooks")
    pre = pre_hooks[0]
    post = post_hooks[0]

    allow_resp = pre(
        {"tool_name": "Read", "tool_input": {"file_path": "README.md"}},
        tool_use_id="tu-1",
    )
    deny_resp = pre(
        {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}},
        tool_use_id="tu-2",
    )
    post(
        {
            "tool_name": "Read",
            "tool_input": {"file_path": "README.md"},
            "tool_response": "ok",
        },
        tool_use_id="tu-1",
    )

    allow_decision = (
        (allow_resp.get("hookSpecificOutput") or {}).get("permissionDecision")
        or allow_resp.get("permission_decision")
        or "allow"
    )
    deny_decision = (
        (deny_resp.get("hookSpecificOutput") or {}).get("permissionDecision")
        or deny_resp.get("permission_decision")
        or "deny"
    )

    print(
        json.dumps(
            {
                "example": "relay_claude_sdk",
                "sessionId": sid,
                "hooksKeys": sorted(hooks.keys()),
                "allowDecision": allow_decision,
                "denyDecision": deny_decision,
                "wire": "ClaudeAgentOptions(hooks=relay.claude_hooks(session_id=...))",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
