# src/llm/__init__.py
import os
from . import client, harness_client
from .custom_client import CustomClient as CustomLLMClient


def get_llm_client():
    """
    Returns a client object with a .chat(system, user) method,
    based on LLM_PROVIDER env variable.
    """
    provider = os.getenv("LLM_PROVIDER", "harness").lower()
    if provider == "harness":
        return _HarnessWrapper()
    elif provider in ("custom", "openai-compatible"):
        return _CustomWrapper()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


class _HarnessWrapper:
    """Wraps the existing functional harness client."""
    def chat(self, system: str, user: str, **kwargs) -> dict:
        return client.chat(system=system, user=user, **kwargs)


class _CustomWrapper:
    """Wraps the OpenAI-compatible client."""
    def __init__(self):
        self._inner = CustomLLMClient()

    def chat(self, system: str, user: str, **kwargs) -> dict:
        text = self._inner.chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        return {
            "text": text,
            "tokens_in": 0,
            "tokens_out": 0,
            "model": self._inner.model,
            "mode": "custom",
        }


__all__ = ["get_llm_client", "CustomLLMClient"]