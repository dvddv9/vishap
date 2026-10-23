# -*- coding: utf-8 -*-
"""Vishap MCP stdio server — local analysis, user's own LLM (any provider)."""
import os
import httpx
from fastmcp import FastMCP

mcp = FastMCP("Vishap")

# LLM config (any OpenAI-compatible endpoint)
LLM_URL = os.getenv("LLM_URL", "https://api.deepseek.com/v1").rstrip("/")
LLM_KEY = os.getenv("LLM_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")


@mcp.tool
def vishap_analyze(material: str, filename: str) -> str:
    """Analyze code / text for security risks (SQLi, XSS, RCE, etc.)."""
    if not LLM_KEY and "localhost" not in LLM_URL and "127.0.0.1" not in LLM_URL:
        return "Error: LLM_KEY is not set. Configure it in extension settings."

    prompt = (
        "You are a security analyzer. Analyze the following material for security risks.\n"
        f"Filename: {filename}\n"
        "Material:\n"
        "```\n"
        f"{material}\n"
        "```\n"
        "Return a structured Markdown report:\n"
        "- Summary (1-2 lines)\n"
        "- Critical risks (with CWE, line numbers, exploitability)\n"
        "- Recommended fixes (parameterized queries, input validation, etc.)\n"
        "- STRIDE threat model (if applicable)\n"
    )

    try:
        headers = {"Content-Type": "application/json"}
        if LLM_KEY:
            headers["Authorization"] = f"Bearer {LLM_KEY}"

        with httpx.Client(timeout=300.0) as client:
            resp = client.post(
                f"{LLM_URL}/chat/completions",
                headers=headers,
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        return f"LLM HTTP error {e.response.status_code}: {e.response.text[:300]}"
    except Exception as e:
        return f"LLM error: {e}"


if __name__ == "__main__":
    mcp.run()
