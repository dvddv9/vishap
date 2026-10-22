# -*- coding: utf-8 -*-
"""Unified LLM entry point (v7.2).

Providers: custom (OpenAI-compatible) | harness.
Selection: VISHAP_LLM_PROVIDER=auto|custom|harness.
auto -> custom if CUSTOM_LLM_* set, else harness.
DeepSeek is reachable via custom: CUSTOM_LLM_URL=https://api.deepseek.com/v1.
"""
from __future__ import annotations

import os

from src.llm._observe import observe_llm_result
from src.llm import harness_client  # noqa: F401 — patched by tests

NO_HARNESS_TEXT = (
    "[LLM error] DSH harness is unreachable: make sure the DSH app is running and "
    "set HARNESS_URL (default http://127.0.0.1:3080) and HARNESS_TOKEN."
)
NO_CUSTOM_TEXT = (
    "[LLM error] custom provider failed: set CUSTOM_LLM_URL / CUSTOM_LLM_KEY / CUSTOM_LLM_MODEL."
)


def _resolve_provider() -> str:
    mode = os.getenv("VISHAP_LLM_PROVIDER", "auto").strip().lower()
    if mode in ("custom", "harness"):
        return mode
    if os.getenv("CUSTOM_LLM_URL", "").strip() and os.getenv("CUSTOM_LLM_KEY", "").strip():
        return "custom"
    return "harness"


def _chat_custom(system: str, user: str, temperature: float, max_tokens: int) -> dict:
    try:
        from src.llm.custom_client import CustomClient
        c = CustomClient()
        try:
            result = c.chat(user, system, temperature=temperature, max_tokens=max_tokens)
        finally:
            c.close()
        return observe_llm_result(result)
    except Exception as e:
        return observe_llm_result({
            "text": f"{NO_CUSTOM_TEXT} ({e})",
            "tokens_in": 0, "tokens_out": 0,
            "model": "none", "mode": "error",
        }, status="error")


def _chat_harness(system: str, user: str) -> dict:
    try:
        from src.llm import harness_client
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


def chat(system: str, user: str,
         temperature: float = 0.0,
         max_tokens: int = 2000) -> dict:
    provider = _resolve_provider()
    if provider == "custom":
        return _chat_custom(system, user, temperature, max_tokens)
    return _chat_harness(system, user)


def current_provider() -> str:
    return _resolve_provider()
