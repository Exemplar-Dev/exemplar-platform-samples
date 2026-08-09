"""Shared helpers for live samples (published SDK only)."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from exemplar_harness import Harness

_ROOT = Path(__file__).resolve().parent
SOURCE_APP = "exemplar-platform-samples"


def load_env() -> None:
    load_dotenv(_ROOT / ".env")
    load_dotenv(_ROOT.parent / ".env")


def require_api_key() -> None:
    load_env()
    if not os.environ.get("EXEMPLAR_API_KEY", "").strip():
        print(
            "Set EXEMPLAR_API_KEY (org key eis_…) before running samples.\n"
            "  cp .env.example .env\n"
            "Docs: https://docs.exemplar.dev/account-settings/tokens-and-api-keys",
            file=sys.stderr,
        )
        raise SystemExit(1)


def harness(agent_id: str = "platform-samples") -> Harness:
    require_api_key()
    return Harness.from_env(agent_id=agent_id)


def session_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"
