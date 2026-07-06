"""Provider clients + cost accounting. Keep pricing in ONE place.

Provider: NVIDIA NIM (OpenAI-compatible endpoint, free tier).
cost_usd is SYNTHETIC — NIM free tier bills nothing; the numbers below
mirror typical market per-token rates so the cost-routing math stays real.
"""
import os
from dataclasses import dataclass

from openai import AsyncOpenAI

# USD per 1M tokens (input, output). Synthetic market-rate equivalents.
PRICING = {
    "meta/llama-3.1-8b-instruct": (0.10, 0.30),
    "meta/llama-3.3-70b-instruct": (0.70, 0.90),
}

_client = AsyncOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY", ""),
)


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
    resp = await _client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    in_tok = resp.usage.prompt_tokens
    out_tok = resp.usage.completion_tokens
    return ModelResult(
        text=resp.choices[0].message.content,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost_usd=compute_cost(model, in_tok, out_tok),
    )
