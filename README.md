# RouteIQ — LLM Cost Router & Observability Gateway

<!-- TODO: add real badges after first push: CI status, Python version -->

Routes every LLM request to the **cheapest model that can handle it**, enforces
per-team budgets in Redis, and traces every token, dollar, and millisecond into
Grafana. Like a taxi dispatcher: no S-Class for a 500-meter trip.

## Headline result

<!-- TODO: replace with YOUR measured numbers from `python evals/run_evals.py` -->
> On a N-prompt eval set, routing cut API cost by **X%** vs. always using the
> strongest model, with quality drop under **Y%** (eval-gated in CI).

## Architecture

```
client ──> FastAPI /v1/chat
             ├─ 1. Redis budget gate (429 if team over budget)
             ├─ 2. complexity classifier ──> cheap | strong model
             ├─ 3. provider call (Anthropic)
             └─ 4. Prometheus metrics ──> Grafana dashboard
```

## Quickstart

```bash
cp .env.example .env        # add your ANTHROPIC_API_KEY
docker compose up --build
curl -X POST localhost:8000/v1/chat -H 'Content-Type: application/json' \
  -d '{"prompt": "What is the capital of Germany?", "team": "demo"}'
# -> routed to the cheap model; check "routing_reason" in the response
```

Grafana: http://localhost:3000 (admin/admin) · Prometheus: http://localhost:9090

## Why it's built this way

- **Redis for budgets, not Postgres** — the gate runs on every request; atomic
  `INCRBYFLOAT` at sub-ms beats a DB round-trip.
- **Eval-gated CI** — any change to routing logic must pass
  `evals/run_evals.py` or the pipeline fails. Cost savings mean nothing if
  quality silently degrades.
- **Heuristic classifier first** — shipped and measured before optimizing.
  v1 replaces it with a learned classifier, justified by eval numbers.

## Roadmap

- [ ] Daily budget reset (TTL keys)
- [ ] OpenTelemetry traces per request
- [ ] LLM-as-judge eval scoring
- [ ] OpenAI provider + cross-provider routing
