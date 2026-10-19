# -*- coding: utf-8 -*-
"""Unified LLM entry point — DSH harness only.

Vishap talks to a local **DeepSeek Harness (DSH)** instance: it creates a session,
sends the prompt and reads the reply out of the session log. Since v7.0.0 there is
no direct DeepSeek / OpenAI / OpenAI-compatible API call — the harness is the only
LLM path, and every stage of the pipeline goes through it.

Configuration comes from the environment (see `.env.example`):

- ``HARNESS_URL``   — where the DSH app listens (default ``http://127.0.0.1:3080``)
- ``HARNESS_TOKEN`` — the token DSH prints at startup
- ``HARNESS_TIMEOUT`` — request timeout in seconds

`temperature` and `max_tokens` are accepted for interface compatibility and are
not forwarded: the harness owns model selection and sampling.
"""

from src.llm import harness_client
from src.llm._observe import observe_llm_result

#: Shown when the harness cannot be reached — names what to fix instead of
#: raising from deep inside the pipeline.
NO_HARNESS_TEXT = (
    "[LLM error] DSH harness is unreachable: make sure the DSH app is running and "
    "set HARNESS_URL (default http://127.0.0.1:3080) and HARNESS_TOKEN."
)


def _resolve_provider() -> str:
    """The harness is the only provider.

    Kept as a function because the API exposes it in diagnostics
    (`/mode`, `current_provider`); it always returns ``"harness"``.
    """
    return "harness"


def chat(system: str, user: str,
         temperature: float = 0.0,
         max_tokens: int = 2000) -> dict:
    """Run one prompt through the harness. Returns {text, tokens_in, tokens_out, model, mode}."""
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
    """Return resolved provider name (for diagnostics)."""
    return _resolve_provider()
