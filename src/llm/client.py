# -*- coding: utf-8 -*-
"""Unified LLM entry point — DSH harness only.

All stages call ``chat()``. It goes to the local DeepSeek Harness (DSH)
instance: create a session, send the prompt, read the reply from the session log.
"""
from __future__ import annotations

from src.llm import harness_client
from src.llm._observe import observe_llm_result

NO_HARNESS_TEXT = (
    "[LLM error] DSH harness is unreachable: make sure the DSH app is running and "
    "set HARNESS_URL (default http://127.0.0.1:3080) and HARNESS_TOKEN."
)


def _resolve_provider() -> str:
    return "harness"


def chat(system: str, user: str,
         temperature: float = 0.0,
         max_tokens: int = 2000) -> dict:
    """Run one prompt through the DSH harness."""
    try:
        h = harness_client.HarnessClient()
        try:
            result = h.chat(user, system)
        finally:
            h.close()
        return observe_llm_result(result)
    except Exception as e:
        return observe_llm_result({
            "text": f"{NO_HARNESS_TEXT} ({e})",
            "tokens_in": 0, "tokens_out": 0,
            "model": "none", "mode": "error",
        }, status="error")


def current_provider() -> str:
    return _resolve_provider()
