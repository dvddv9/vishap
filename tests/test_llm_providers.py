# -*- coding: utf-8 -*-
"""LLM layer: the DSH harness is the only provider (v7.0.0).

There is no direct DeepSeek / OpenAI / OpenAI-compatible call any more, so these
tests pin the new contract: one provider, one call path, one error shape.

The harness owns model selection, so `temperature` / `max_tokens` are accepted by
`chat()` for interface compatibility but are not forwarded.
"""
from unittest.mock import MagicMock, patch

from src.llm import client


def _patch_harness(chat_result=None, side_effect=None):
    """Patch HarnessClient so `chat()` gets a predictable instance."""
    instance = MagicMock()
    if side_effect is not None:
        instance.chat.side_effect = side_effect
    else:
        instance.chat.return_value = chat_result
    return patch("src.llm.client.harness_client.HarnessClient", return_value=instance), instance


def test_resolve_provider_auto(monkeypatch):
    # An old .env value must not resurrect a removed provider.
    monkeypatch.setenv("VISHAP_LLM_PROVIDER", "auto")
    # v7.2: auto -> custom if CUSTOM_LLM_* set, else harness
    assert client._resolve_provider() in ("custom", "harness")


def test_chat_calls_harness_with_user_then_system(monkeypatch):
    monkeypatch.setenv("VISHAP_LLM_PROVIDER", "harness")
    patcher, instance = _patch_harness({"text": "ok", "model": "harness",
                                        "tokens_in": 0, "tokens_out": 0,
                                        "mode": "harness"})
    with patcher:
        result = client.chat("SYSTEM", "USER")
    # HarnessClient.chat takes (user, system) -- the opposite of the old clients.
    instance.chat.assert_called_once_with("USER", "SYSTEM")
    assert result["text"] == "ok"


def test_chat_returns_error_dict_when_harness_is_unreachable(monkeypatch):
    monkeypatch.setenv("VISHAP_LLM_PROVIDER", "harness")
    patcher, _ = _patch_harness(side_effect=RuntimeError("HARNESS_TOKEN empty"))
    with patcher:
        result = client.chat("s", "u")
    assert result["mode"] == "error"
    assert "HARNESS_TOKEN" in result["text"]
    assert result["model"] == "none"


def test_chat_closes_the_client(monkeypatch):
    monkeypatch.setenv("VISHAP_LLM_PROVIDER", "harness")
    patcher, instance = _patch_harness({"text": "ok", "model": "harness",
                                        "tokens_in": 0, "tokens_out": 0,
                                        "mode": "harness"})
    with patcher:
        client.chat("s", "u")
    instance.close.assert_called_once()


def test_no_provider_string_mentions_the_fix():
    assert "HARNESS_URL" in client.NO_HARNESS_TEXT
    assert "HARNESS_TOKEN" in client.NO_HARNESS_TEXT


def test_async_chat_uses_harness_client():
    from src.llm import async_client
    import asyncio

    instance = MagicMock()
    instance.chat.return_value = {"text": "async-ok", "model": "harness",
                                  "tokens_in": 0, "tokens_out": 0, "mode": "harness"}
    with patch("src.llm.async_client.harness_client.HarnessClient", return_value=instance):
        result = asyncio.run(async_client.async_chat("SYSTEM", "USER"))
    instance.chat.assert_called_once_with("USER", "SYSTEM")
    assert result["text"] == "async-ok"


def test_env_example_documents_harness_vars():
    from pathlib import Path
    content = Path(".env.example").read_text(encoding="utf-8")
    assert "HARNESS_URL" in content
    assert "HARNESS_TOKEN" in content
    # The removed providers must not be advertised any more.
    assert "DEEPSEEK_API_KEY" not in content
    assert "VISHAP_LLM_PROVIDER" not in content


def test_mode_is_fixed_to_harness():
    from src.storage.mode import DEFAULT_MODE, VALID_MODES
    assert VALID_MODES == ("harness",)
    assert DEFAULT_MODE == "harness"
