# -*- coding: utf-8 -*-
"""OpenAI-compatible custom provider (Groq / OpenAI / DeepSeek via custom)."""
from __future__ import annotations

import os
import json  # noqa: F401  # (if needed)

# v7.3.1: Claude 5.x deprecates `temperature` (HTTP 400).
# Set CUSTOM_LLM_SEND_TEMPERATURE=false for Claude 5.x.
SEND_TEMPERATURE = os.getenv("CUSTOM_LLM_SEND_TEMPERATURE", "true").lower() == "true"

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_URL = os.getenv("CUSTOM_LLM_URL", "")
DEFAULT_KEY = os.getenv("CUSTOM_LLM_KEY", "")
DEFAULT_MODEL = os.getenv("CUSTOM_LLM_MODEL", "")
DEFAULT_TIMEOUT = float(os.getenv("CUSTOM_LLM_TIMEOUT", "120"))


class CustomError(RuntimeError):
    """Any error talking to the custom OpenAI-compatible endpoint."""


class CustomClient:
    def __init__(self, base_url: str | None = None,
                 api_key: str | None = None,
                 model: str | None = None,
                 timeout: float | None = None) -> None:
        self.base_url = (base_url or DEFAULT_URL).rstrip("/")
        self.api_key = api_key or DEFAULT_KEY
        self.model = model or DEFAULT_MODEL
        self.timeout = timeout or DEFAULT_TIMEOUT
        if not self.base_url:
            raise CustomError("CUSTOM_LLM_URL is empty")
        if not self.api_key:
            raise CustomError("CUSTOM_LLM_KEY is empty")
        if not self.model:
            raise CustomError("CUSTOM_LLM_MODEL is empty")

    def chat(self, user: str, system: str = "",
             temperature: float = 0.0, max_tokens: int = 2000) -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        payload = {
            "model": self.model,
            "messages": messages,
            # v7.3.1: skip temperature if CUSTOM_LLM_SEND_TEMPERATURE=false
            **({"temperature": temperature} if SEND_TEMPERATURE else {}),
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            r = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload, headers=headers, timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise CustomError(f"custom request failed: {e}") from e
        if r.status_code != 200:
            raise CustomError(f"custom HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        try:
            text = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError) as e:
            raise CustomError(f"unexpected custom response: {e}") from e
        usage = data.get("usage") or {}
        return {
            "text": text,
            "tokens_in": int(usage.get("prompt_tokens", 0) or 0),
            "tokens_out": int(usage.get("completion_tokens", 0) or 0),
            "model": data.get("model", self.model),
            "mode": "custom",
        }

    def close(self) -> None:
        pass


# backward compat
CustomLLMClient = CustomClient
