# -*- coding: utf-8 -*-
"""Cost tracking for LLM calls (USD per 1M tokens).

Since v7.0.0 every call goes through the local DSH harness, which does not report
token counts back to Vishap — so stage costs are `0.0` and this table exists only
for the historical/mock paths. If a harness ever returns token usage, add its
price row here.
"""

# Prices per 1M tokens (USD)
PRICES = {
    "harness":           {"in": 0.0,  "out": 0.0},
    "default":           {"in": 0.0,  "out": 0.0},
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Returns cost in USD (rounded to 6 decimals)."""
    p = PRICES.get(model, PRICES["default"])
    cost = (tokens_in * p["in"] + tokens_out * p["out"]) / 1_000_000
    return round(cost, 6)


def sum_stage_costs(stages: list) -> float:
    """Sum cost_usd from stages _meta. Skips None."""
    total = 0.0
    for s in stages:
        if not isinstance(s, dict):
            continue
        meta = s.get("_meta", {})
        total += meta.get("cost_usd", 0.0)
    return round(total, 6)
