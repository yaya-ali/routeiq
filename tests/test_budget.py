"""Budget gate tests — run against a fake in-memory redis, no server needed."""
import app.budget as budget


class FakeRedis:
    def __init__(self):
        self.store: dict[str, float] = {}
        self.ttls: dict[str, int] = {}

    def incrbyfloat(self, key: str, amount: float) -> float:
        self.store[key] = float(self.store.get(key, 0.0)) + amount
        return self.store[key]

    def expire(self, key: str, seconds: int, nx: bool = False) -> bool:
        if nx and key in self.ttls:
            return False
        self.ttls[key] = seconds
        return True


def test_under_budget_allowed(monkeypatch):
    monkeypatch.setattr(budget, "_r", FakeRedis())
    allowed, remaining = budget.check_and_charge("teamA", 1.0)
    assert allowed
    assert remaining == budget.DAILY_BUDGET_USD - 1.0


def test_over_budget_blocked(monkeypatch):
    monkeypatch.setattr(budget, "_r", FakeRedis())
    budget.check_and_charge("teamA", budget.DAILY_BUDGET_USD)
    allowed, remaining = budget.check_and_charge("teamA", 0.0)
    assert not allowed
    assert remaining <= 0


def test_budget_resets_next_day(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(budget, "_r", fake)
    monkeypatch.setattr(budget, "_today", lambda: "2026-07-06")
    budget.check_and_charge("teamA", budget.DAILY_BUDGET_USD)  # exhaust today

    monkeypatch.setattr(budget, "_today", lambda: "2026-07-07")  # next day
    allowed, remaining = budget.check_and_charge("teamA", 0.01)
    assert allowed
    assert remaining > 0


def test_teams_are_isolated(monkeypatch):
    monkeypatch.setattr(budget, "_r", FakeRedis())
    budget.check_and_charge("teamA", budget.DAILY_BUDGET_USD)
    allowed, _ = budget.check_and_charge("teamB", 0.01)
    assert allowed


def test_key_gets_ttl(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(budget, "_r", fake)
    budget.check_and_charge("teamA", 0.01)
    key = f"spend:teamA:{budget._today()}"
    assert fake.ttls[key] == 60 * 60 * 48
