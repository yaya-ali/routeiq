"""Per-team budget enforcement in Redis — the taxi meter.

Design decision to defend in interviews: budgets live in Redis (not Postgres)
because every single request hits this check — it must be sub-millisecond,
and atomic INCRBYFLOAT avoids race conditions between concurrent requests.
"""
import os
from datetime import datetime, timezone

import redis

DAILY_BUDGET_USD = float(os.environ.get("DAILY_BUDGET_USD", "5.0"))

_r = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, decode_responses=True)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def check_and_charge(team: str, estimated_cost: float) -> tuple[bool, float]:
    """Atomically add cost to today's spend. Returns (allowed, remaining_usd).

    The date in the key is what resets the budget: tomorrow's requests hit a
    fresh key. The TTL is only garbage collection for yesterday's keys.
    """
    key = f"spend:{team}:{_today()}"
    spent = float(_r.incrbyfloat(key, estimated_cost))
    _r.expire(key, 60 * 60 * 48, nx=True)
    remaining = DAILY_BUDGET_USD - spent
    return remaining > 0, remaining
