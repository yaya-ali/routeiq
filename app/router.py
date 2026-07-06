"""Complexity classifier — THE core of RouteIQ. This is your interview material.

The dispatcher: judge how hard the trip is, send the cheapest car that can do it.

MVP = heuristic rules (ship this first, it works).
v1  = replace with a small classifier model or LLM-as-judge, and PROVE the
      upgrade helped using the eval suite (evals/run_evals.py).
"""

CHEAP = "claude-haiku-4-5-20251001"      # small cab
STRONG = "claude-sonnet-5"               # S-Class

# Signals that a prompt needs the strong model.
REASONING_HINTS = (
    "step by step", "prove", "analyze", "compare", "trade-off", "architecture",
    "debug", "why does", "explain the difference", "optimize",
)
CODE_HINTS = ("```", "def ", "class ", "SELECT ", "import ", "function", "traceback")


def choose_model(prompt: str) -> tuple[str, str]:
    """Return (model_id, human-readable reason).

    TODO(you): tune these thresholds against the eval set — do NOT guess.
    Run `python evals/run_evals.py` after every change and keep a table of
    results in the README. That table IS the project.
    """
    p = prompt.lower()

    if len(prompt) > 2000:
        return STRONG, "long context (>2000 chars)"
    if any(h in p for h in REASONING_HINTS):
        return STRONG, "reasoning keywords detected"
    if any(h in prompt for h in CODE_HINTS):
        return STRONG, "code content detected"
    if prompt.count("?") >= 3:
        return STRONG, "multi-question prompt"

    return CHEAP, "simple query — routed to cheap model"
