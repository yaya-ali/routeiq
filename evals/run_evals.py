"""Eval suite — proves routing saves money WITHOUT losing quality.

This produces the README's headline number:
  "Router cut cost X% vs always-strong, quality drop < Y%"

Method: run every prompt in cases.json through (a) the router and
(b) always-STRONG. Compare cost and quality. Exit non-zero if quality
drops more than the threshold -> CI blocks the merge.
"""
import asyncio
import json
import pathlib
import sys

from app.providers import call_model
from app.router import STRONG, choose_model

QUALITY_DROP_THRESHOLD = 0.05  # 5% max acceptable quality loss

CASES = json.loads((pathlib.Path(__file__).parent / "cases.json").read_text())


def score(answer: str, case: dict) -> float:
    """MVP scoring: keyword coverage. v1: LLM-as-judge with rubric.

    TODO(you): this is deliberately simple. Upgrade it and show before/after
    in the README — evaluating the evaluator is exactly what interviewers probe.
    """
    hits = sum(1 for kw in case["must_contain"] if kw.lower() in answer.lower())
    return hits / len(case["must_contain"])


async def run() -> None:
    routed_cost = strong_cost = 0.0
    routed_q, strong_q = [], []

    for case in CASES:
        model, _ = choose_model(case["prompt"])
        r = await call_model(model, case["prompt"])
        s = await call_model(STRONG, case["prompt"])
        routed_cost += r.cost_usd
        strong_cost += s.cost_usd
        routed_q.append(score(r.text, case))
        strong_q.append(score(s.text, case))

    rq, sq = sum(routed_q) / len(routed_q), sum(strong_q) / len(strong_q)
    saved = 1 - routed_cost / strong_cost
    drop = sq - rq

    print(f"cost: routed=${routed_cost:.4f} strong=${strong_cost:.4f} saved={saved:.1%}")
    print(f"quality: routed={rq:.2f} strong={sq:.2f} drop={drop:.2%}")

    if drop > QUALITY_DROP_THRESHOLD:
        print("FAIL: quality dropped past threshold — routing too aggressive")
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    asyncio.run(run())
