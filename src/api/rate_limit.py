# -*- coding: utf-8 -*-
"""Simple in-memory rate limiter (dogfood P0 fix).

Dogfood finding: no rate limiting on /analyze -> any client could
exhaust the local harness (one model, no queue of its own).

Limits (per IP):
- 10 requests / minute for /analyze, /analyze/batch
- 30 requests / minute for /history, /mode
"""
import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status


_BUCKETS = defaultdict(deque)

LIMIT_ANALYZE = 10
LIMIT_READ = 30
WINDOW_SECONDS = 60


def _check(key: str, limit: int) -> None:
    now = time.time()
    bucket = _BUCKETS[key]

    while bucket and bucket[0] < now - WINDOW_SECONDS:
        bucket.popleft()

    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: {} req / {}s".format(limit, WINDOW_SECONDS),
        )

    bucket.append(now)


async def rate_limit_analyze(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    _check("analyze:" + ip, LIMIT_ANALYZE)


async def rate_limit_read(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    _check("read:" + ip, LIMIT_READ)