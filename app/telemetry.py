"""Observability — the dashcam. Prometheus metrics now, OTel traces in v1."""
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, make_asgi_app

REQUESTS = Counter("routeiq_requests_total", "Requests by model and team", ["model", "team"])
COST = Counter("routeiq_cost_usd_total", "Cumulative USD spend", ["model", "team"])
LATENCY = Histogram("routeiq_latency_ms", "Provider latency ms", ["model"],
                    buckets=(100, 250, 500, 1000, 2000, 5000, 10000))
TOKENS = Counter("routeiq_output_tokens_total", "Output tokens", ["model"])


def setup_telemetry(app: FastAPI) -> None:
    # Exposes /metrics for Prometheus to scrape.
    app.mount("/metrics", make_asgi_app())
    # TODO(you, v1): add OpenTelemetry FastAPIInstrumentor here so every request
    # produces a trace: budget check -> routing decision -> provider call.


def record_request(model: str, team: str, cost: float, latency_ms: int, tokens: int) -> None:
    REQUESTS.labels(model=model, team=team).inc()
    COST.labels(model=model, team=team).inc(cost)
    LATENCY.labels(model=model).observe(latency_ms)
    TOKENS.labels(model=model).inc(tokens)
