# -*- coding: utf-8 -*-
"""
Стадии pipeline Vishap.
v2: улучшенный JSON-парсинг + max_tokens из config.
"""
import json
import re
from src.llm.client import chat as llm_chat
from src.pipeline.prompts import build_prompt
from src.config import MAX_TOKENS, MAX_TOKENS_STAGE4, ENABLE_WEB_SEARCH
from src.tools.web_search import search_many, is_enabled as web_search_enabled


def _clean_json_string(text: str) -> str:
    result = []
    in_string = False
    escape = False
    i = 0
    while i < len(text):
        ch = text[i]

        if escape:
            result.append(ch)
            escape = False
            i += 1
            continue

        if ch == "\\":
            result.append(ch)
            escape = True
            i += 1
            continue

        if ch == '"':
            in_string = not in_string
            result.append(ch)
            i += 1
            continue

        if not in_string:
            if ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue
            if ch == "/" and i + 1 < len(text) and text[i + 1] == "*":
                i += 2
                while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2
                continue

        result.append(ch)
        i += 1

    return "".join(result)


def _try_parse(text: str) -> dict | None:
    if not text or not text.strip():
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    cleaned = _clean_json_string(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    no_trailing = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        return json.loads(no_trailing)
    except json.JSONDecodeError:
        pass

    start = no_trailing.find("{")
    end = no_trailing.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(no_trailing[start:end + 1])
        except json.JSONDecodeError:
            pass

    start = no_trailing.find("[")
    end = no_trailing.rfind("]")
    if start >= 0 and end > start:
        try:
            return json.loads(no_trailing[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def parse_json_response(text: str) -> dict:
    text = text.strip()

    code_block_patterns = [
        r"```json\s*\n?(.*?)\n?```",
        r"```\s*\n?(.*?)\n?```",
    ]
    for pattern in code_block_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(1).strip()
            parsed = _try_parse(candidate)
            if parsed is not None:
                return parsed
            break

    parsed = _try_parse(text)
    if parsed is not None:
        return parsed

    return {
        "_raw": text[:5000],
        "_error": "JSON parse failed",
        "_raw_length": len(text),
    }


def run_stage(stage_name: str, prompt_name: str, material: str,
              context: dict | None = None,
              temperature: float = 0.0,
              max_tokens: int | None = None,
              retry_on_json_fail: bool = True,
              web_search_results: list | None = None) -> dict:
    if max_tokens is None:
        max_tokens = MAX_TOKENS

    system, user = build_prompt(prompt_name, material, context, web_search_results)

    result = llm_chat(system, user, temperature=temperature, max_tokens=max_tokens)
    parsed = parse_json_response(result["text"])

    if retry_on_json_fail and "_error" in parsed and parsed["_error"] == "JSON parse failed":
        print(f"  [!] {stage_name}: JSON parse failed, retry...")
        retry_user = (
            user
            + "\n\n## ВАЖНО\n\n"
            + "Верни ТОЛЬКО валидный JSON без Markdown, без комментариев, "
            + "без текста до или после. Только { ... }."
        )
        result = llm_chat(system, retry_user, temperature=temperature, max_tokens=max_tokens)
        parsed = parse_json_response(result["text"])

    from src.pipeline.cost import estimate_cost

    # === FIX: ensure parsed is dict ===
    if not isinstance(parsed, dict):
        parsed = {"_raw": parsed, "_error": "expected dict, got list"}

    parsed["_meta"] = {
        "stage": stage_name,
        "tokens_in": result["tokens_in"],
        "tokens_out": result["tokens_out"],
        "model": result["model"],
        "mode": result["mode"],
        "json_ok": "_error" not in parsed,
        "cost_usd": estimate_cost(
            result["model"], result["tokens_in"], result["tokens_out"]
        ),
    }
    return parsed




def stage0_orchestrator(material: str, filename: str) -> dict:
    return run_stage(
        stage_name="stage0_orchestrator",
        prompt_name="00_orchestrator",
        material=f"# File: {filename}\n\n{material}",
        temperature=0.0,
        max_tokens=2000,
    )


def stage1_scanner(material: str, context: dict) -> dict:
    return run_stage(
        stage_name="stage1_scanner",
        prompt_name="01_scanner",
        material=material,
        context=context,
        temperature=0.0,
    )


def stage2_analyst(material: str, context: dict,
                   search_queries: list | None = None) -> dict:
    """Stage 2: Analyst с опциональным web search."""
    web_search_results = None
    queries_used = []

    if ENABLE_WEB_SEARCH and web_search_enabled():
        queries_used = search_queries or _generate_default_queries(material)
        if queries_used:
            print(f"  [Web Search] {len(queries_used)} queries...")
            web_search_results = search_many(queries_used)
            print(f"  [Web Search] {len(web_search_results)} results")

    result = run_stage(
        stage_name="stage2_analyst",
        prompt_name="02_analyst",
        material=material,
        context=context,
        temperature=0.0,
        web_search_results=web_search_results,
    )

    result["_web_search"] = {
        "used": bool(web_search_results),
        "queries": queries_used,
        "credits": len(queries_used),
    }
    return result


def _generate_default_queries(material: str) -> list:
    """Простая эвристика — 1-3 запроса из материала."""
    queries = []
    m = material.lower()

    if "sql" in m or "cwe-89" in m:
        queries.append("SQL injection prevention best practices 2026")
    if "xss" in m or "cwe-79" in m:
        queries.append("XSS prevention Content Security Policy best practices")
    if "buffer overflow" in m or "cwe-122" in m:
        queries.append("heap buffer overflow mitigation best practices")
    if "kafka" in m:
        queries.append("Kafka at-least-once deduplication best practices")
    if "redis" in m:
        queries.append("Redis idempotency anti-patterns")
    if "gdpr" in m:
        queries.append("GDPR Article 17 right to erasure implementation")
    if "pci" in m:
        queries.append("PCI DSS requirement 6.5 secure coding")

    if not queries:
        queries.append("recent CVEs and security best practices")

    return queries[:3]


def stage3_researcher(material: str, context: dict) -> dict:
    return run_stage(
        stage_name="stage3_researcher",
        prompt_name="03_researcher",
        material=material,
        context=context,
        temperature=0.3,
    )


def stage4_synthesizer(material: str, context: dict) -> dict:
    return run_stage(
        stage_name="stage4_synthesizer",
        prompt_name="04_synthesizer",
        material=material,
        context=context,
        temperature=0.0,
        max_tokens=MAX_TOKENS_STAGE4,
    )


def stage5_transmitter(material: str, context: dict) -> str:
    system, user = build_prompt("05_transmitter", material, context)
    result = llm_chat(system, user, temperature=0.0, max_tokens=MAX_TOKENS)
    return result["text"]



