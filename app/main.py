"""RouteIQ — LLM cost router & observability gateway.

Request flow:  client -> /v1/chat -> budget check -> complexity classifier
               -> model selection -> provider call -> metrics/trace -> response
"""
import pathlib
import time

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.budget import check_and_charge
from app.providers import PRICING, call_model
from app.router import choose_model
from app.telemetry import record_request, setup_telemetry

app = FastAPI(title="RouteIQ", version="0.1.0")
setup_telemetry(app)


class ChatRequest(BaseModel):
    prompt: str
    team: str = "default"
    force_model: str | None = None  # escape hatch for debugging


class ChatResponse(BaseModel):
    answer: str
    model_used: str
    routing_reason: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/demo", response_class=HTMLResponse)
def demo() -> str:
    # Example consumer app: quiz generator with zero AI code of its own.
    return (pathlib.Path(__file__).parent / "static" / "demo.html").read_text()


@app.get("/chat", response_class=HTMLResponse)
def chat_ui() -> str:
    # Minimal chat UI for non-technical testing; conversation context is
    # client-side (the gateway itself stays stateless).
    return (pathlib.Path(__file__).parent / "static" / "chat.html").read_text()


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, x_api_key: str = Header(default="anon")) -> ChatResponse:
    # 1. Budget gate — the taxi meter. Reject before spending money.
    allowed, remaining = check_and_charge(team=req.team, estimated_cost=0.0)
    if not allowed:
        raise HTTPException(status_code=429, detail=f"Budget exhausted for team '{req.team}'")

    # 2. Dispatcher — decide which car to send for this trip.
    if req.force_model and req.force_model not in PRICING:
        raise HTTPException(status_code=400,
                            detail=f"Unknown model '{req.force_model}'. Valid: {sorted(PRICING)}")
    model, reason = (req.force_model, "forced") if req.force_model else choose_model(req.prompt)

    # 3. Drive.
    t0 = time.perf_counter()
    result = await call_model(model=model, prompt=req.prompt)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    # 4. Charge the real cost + dashcam.
    check_and_charge(team=req.team, estimated_cost=result.cost_usd)
    record_request(model=model, team=req.team, cost=result.cost_usd,
                   latency_ms=latency_ms, tokens=result.output_tokens)

    return ChatResponse(
        answer=result.text,
        model_used=model,
        routing_reason=reason,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=round(result.cost_usd, 6),
        latency_ms=latency_ms,
    )
