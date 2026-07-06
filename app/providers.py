"""Provider clients + cost accounting. Keep pricing in ONE place."""
import os
from dataclasses import dataclass

import anthropic

# USD per 1M tokens (input, output). TODO(you): verify current pricing.
PRICING = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-5": (3.00, 15.00),
}

_client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


@dataclass
class ModelResult:
    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


def compute_cost(model: str, in_tok: int, out_tok: int) -> float:
    pin, pout = PRICING[model]
    return (in_tok * pin + out_tok * pout) / 1_000_000


async def call_model(model: str, prompt: str) -> ModelResult:
    resp = await _client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    in_tok = resp.usage.input_tokens
    out_tok = resp.usage.output_tokens
    return ModelResult(
        text=resp.content[0].text,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost_usd=compute_cost(model, in_tok, out_tok),
    )
