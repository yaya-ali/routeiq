"""Per-team budget enforcement in Redis — the taxi meter.

Design decision to defend in interviews: budgets live in Redis (not Postgres)
because every single request hits this check — it must be sub-millisecond,
and atomic INCRBYFLOAT avoids race conditions between concurrent requests.
"""
import os

import redis

DAILY_BUDGET_USD = float(os.environ.get("DAILY_BUDGET_USD", "5.0"))

_r = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, decode_responses=True)


def check_and_charge(team: str, estimated_cost: float) -> tuple[bool, float]:
    """Atomically add cost to today's spend. Returns (allowed, remaining_usd).

    TODO(you): key should include the date (spend:{team}:{YYYY-MM-DD}) with a
    24h TTL so budgets reset daily. Implement that and add a test for it.
    """
    key = f"spend:{team}"
    spent = float(_r.incrbyfloat(key, estimated_cost))
    remaining = DAILY_BUDGET_USD - spent
    return remaining > 0, remaining
