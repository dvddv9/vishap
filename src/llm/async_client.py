# -*- coding: utf-8 -*-
"""Async LLM entry point — DSH harness only.

The harness client is synchronous (HTTP + polling a session log), so it runs in a
worker thread. This is the async twin of `src.llm.client.chat`: same configuration,
same error contract.
"""
import asyncio

from src.llm import harness_client
from src.llm._observe import observe_llm_result
from src.llm.client import NO_HARNESS_TEXT


async def async_chat(system: str, user: str,
                     temperature: float = 0.0,
                     max_tokens: int = 2000) -> dict:
    """Async LLM entry point — custom (DeepSeek) or DSH harness.

    Mirrors `src.llm.client.chat`: provider is resolved via
    `_resolve_provider()` (VISHAP_LLM_PROVIDER=auto|custom|harness).
    """
    from src.llm.client import _resolve_provider, _chat_custom
    provider = _resolve_provider()
    loop = asyncio.get_event_loop()

    if provider == "custom":
        return await loop.run_in_executor(
            None, lambda: _chat_custom(system, user, temperature, max_tokens),
        )

    try:
        h = harness_client.HarnessClient()
        result = await loop.run_in_executor(None, lambda: h.chat(user, system))
        return observe_llm_result(result)
    except Exception as e:
        return observe_llm_result({
            "text": f"{NO_HARNESS_TEXT} ({e})",
            "tokens_in": 0, "tokens_out": 0,
            "model": "none", "mode": "error",
        }, status="error")
