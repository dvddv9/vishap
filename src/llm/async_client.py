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
    """Асинхронный вызов LLM через DSH harness. Аналог chat()."""
    try:
        h = harness_client.HarnessClient()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: h.chat(user, system))
        return observe_llm_result(result)
    except Exception as e:
        return observe_llm_result({
            "text": f"{NO_HARNESS_TEXT} ({e})",
            "tokens_in": 0, "tokens_out": 0,
            "model": "none", "mode": "error",
        }, status="error")
