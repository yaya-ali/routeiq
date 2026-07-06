# RouteIQ — LLM Cost Router & Observability Gateway

[![ci](https://github.com/yaya-ali/routeiq/actions/workflows/ci.yml/badge.svg)](https://github.com/yaya-ali/routeiq/actions/workflows/ci.yml)

Routes every LLM request to the **cheapest model that can handle it**, enforces
per-team daily budgets in Redis, and traces every token, dollar, and millisecond
into Grafana. Like a taxi dispatcher: no S-Class for a 500-meter trip.

## Headline result

> On a 5-prompt eval set, routing cut API cost by **10.2%** vs. always using the
> strongest model, with **0.00%** quality drop (eval-gated in CI: quality
> regressions past 5% block the merge). Savings scale with the share of simple
> traffic — this set is deliberately reasoning-heavy.

## Architecture

```
client ──> FastAPI /v1/chat
             ├─ 1. Redis budget gate (429 if team over daily budget, resets at UTC midnight)
             ├─ 2. complexity classifier ──> cheap (Llama 3.1 8B) | strong (Llama 3.3 70B)
             ├─ 3. provider call (NVIDIA NIM, OpenAI-compatible API)
             └─ 4. Prometheus metrics ──> Grafana dashboard
```

Provider is NVIDIA NIM's free tier — `cost_usd` uses market-rate-equivalent
per-token pricing so the cost-routing math stays realistic. Swapping providers
touches one file (`app/providers.py`).

## Quickstart

```bash
cp .env.example .env        # add your NVIDIA_API_KEY (free at build.nvidia.com)
docker compose up --build
curl -X POST localhost:8000/v1/chat -H 'Content-Type: application/json' \
  -d '{"prompt": "What is the capital of Germany?", "team": "demo"}'
# -> routed to the cheap model; check "routing_reason" in the response
```

- Swagger UI: http://localhost:8000/docs
- Grafana dashboard: http://localhost:3001 (anonymous viewer, auto-provisioned)
- Prometheus: http://localhost:9090

## Why it's built this way

- **Redis for budgets, not Postgres** — the gate runs on every request; atomic
  `INCRBYFLOAT` at sub-ms beats a DB round-trip.
- **Date-keyed budgets** (`spend:{team}:{YYYY-MM-DD}`) — the date in the key IS
  the daily reset; TTL is just garbage collection. No cron, no race conditions.
- **Eval-gated CI** — any change to routing logic must pass
  `evals/run_evals.py` or the pipeline fails. Cost savings mean nothing if
  quality silently degrades.
- **Heuristic classifier first** — shipped and measured before optimizing.
  v1 replaces it with a learned classifier, justified by eval numbers.

## Tests

```bash
docker compose exec api pytest tests/ -v   # router + budget unit tests
docker compose exec api python evals/run_evals.py  # cost/quality eval (calls the API)
```

## Roadmap

- [x] Heuristic complexity router with per-request routing reason
- [x] Daily budget reset (date-keyed Redis, TTL cleanup)
- [x] Prometheus metrics + provisioned Grafana dashboard
- [x] Eval suite comparing routed vs always-strong
- [ ] OpenTelemetry traces per request
- [ ] LLM-as-judge eval scoring (current: keyword coverage)
- [ ] Cross-provider routing (Anthropic / OpenAI backends)
