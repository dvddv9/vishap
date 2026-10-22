# src/llm/custom_client.py
import os
import httpx


class LLMError(Exception):
    """Raised when a custom LLM request fails."""
    pass


class CustomLLMClient:
    """OpenAI-compatible client (OpenAI, Mistral, Groq, Together, OpenRouter, etc.)."""

    def __init__(self):
        self.base_url = os.getenv("CUSTOM_LLM_URL", "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.getenv("CUSTOM_LLM_KEY", "")
        self.model = os.getenv("CUSTOM_LLM_MODEL", "gpt-4o-mini")
        if not self.api_key:
            raise ValueError("CUSTOM_LLM_KEY is empty")
        self.client = httpx.Client(timeout=120.0)

    def chat(self, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 4096,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        r = self.client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
        if r.status_code != 200:
            raise LLMError(f"{self.model}: HTTP {r.status_code}: {r.text[:200]}")
        return r.json()["choices"][0]["message"]["content"]