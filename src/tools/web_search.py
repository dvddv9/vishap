# -*- coding: utf-8 -*-
"""
Tavily Web Search wrapper для Vishap.
Используется в Stage 2 (Analyst) для поиска свежих CVE, патчей, best practices.

ENABLE_WEB_SEARCH контролирует, выполняется ли поиск.
Если ключ не задан или поиск отключён — search() возвращает {"error": "..."}.
"""
import time
import logging

from src.config import (
    TAVILY_API_KEY,
    ENABLE_WEB_SEARCH,
    SEARCH_MAX_RESULTS,
    SEARCH_DEPTH,
)

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazy-init Tavily client. None if disabled or no key."""
    global _client
    if _client is None:
        if not ENABLE_WEB_SEARCH:
            return None
        if not TAVILY_API_KEY:
            logger.warning("[WebSearch] TAVILY_API_KEY not set — search disabled")
            return None
        try:
            from tavily import TavilyClient
            _client = TavilyClient(api_key=TAVILY_API_KEY)
            logger.info("[WebSearch] Tavily client initialized")
        except Exception as e:
            logger.error(f"[WebSearch] Failed to init Tavily: {e}")
            return None
    return _client


def is_enabled() -> bool:
    """True если поиск включён и клиент доступен."""
    return ENABLE_WEB_SEARCH and bool(TAVILY_API_KEY)


def search(query: str) -> dict:
    """
    Выполнить веб-поиск через Tavily.

    Returns:
        dict: {"results": [...], "query": "..."} при успехе.
              {"error": "...", "query": "..."} при ошибке.
    """
    if not is_enabled():
        return {"error": "web_search_disabled", "query": query}

    client = _get_client()
    if client is None:
        return {"error": "no_client", "query": query}

    try:
        response = client.search(
            query=query,
            max_results=SEARCH_MAX_RESULTS,
            search_depth=SEARCH_DEPTH,
        )
        response["query"] = query
        return response
    except Exception as e:
        logger.warning(f"[WebSearch] search('{query}') failed: {e}")
        return {"error": str(e), "query": query}


def search_many(queries: list, delay: float = 1.0) -> list:
    """
    Выполнить несколько запросов с задержкой (rate limit free tier).

    Args:
        queries: список поисковых запросов
        delay: секунд между запросами (free tier = 1 req/sec)

    Returns:
        list[dict]: список результатов (только успешные).
    """
    results = []
    for i, q in enumerate(queries):
        r = search(q)
        if "error" not in r:
            results.append(r)
        else:
            logger.warning(f"[WebSearch] query {i+1}/{len(queries)} failed: {r.get('error')}")
        if i < len(queries) - 1:
            time.sleep(delay)
    return results