# API Reference

Base URL: `http://localhost:5001`

Most `/analyze*` endpoints accept an optional API key (`X-API-Key`) when `CONVEYOR_API_KEY` is set.

## `GET /health`

Liveness probe.

```bash
curl http://localhost:5001/health
```

```json
{"status": "ok", "timestamp": "2026-10-16T12:00:00"}
```

## `POST /analyze`

Run the full pipeline synchronously.

- **Auth:** optional `X-API-Key` (when `CONVEYOR_API_KEY` is set)

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"material": "def f(): pass", "filename": "x.py"}'
```

```json
{
  "session_id": "sess-2026-10-16-120000",
  "filename": "x.py",
  "level": "D0",
  "final_markdown": "# D0 — f()\n...",
  "audit": {"material_hash": "sha256:...", "critique_verdict": "SAFE"}
}
```

Errors: `400` empty material, `500` pipeline error.

## `POST /analyze/async`

Enqueue an analysis job (Celery + Redis; falls back to an in-process background task when the broker is unavailable).

- **Auth:** optional `X-API-Key`

```bash
curl -X POST http://localhost:5001/analyze/async \
  -H "Content-Type: application/json" \
  -d '{"material": "def f(): pass", "filename": "x.py"}'
```

```json
{"job_id": "job-abc123def456", "status": "queued"}
```

## `GET /status/{job_id}`

```bash
curl http://localhost:5001/status/job-abc123def456
```

```json
{
  "job_id": "job-abc123def456",
  "status": "done",
  "filename": "x.py",
  "created_at": "...",
  "started_at": "...",
  "finished_at": "...",
  "error": null
}
```

Errors: `404` job not found.

## `GET /report/{job_id}`

```bash
curl http://localhost:5001/report/job-abc123def456
```

Returns the full result object.

Errors: `404` job not found, `409` job not done yet.

## `POST /analyze/secure`

Clerk-authenticated variant of `/analyze` (multi-tenant).

- **Auth:** `Authorization: Bearer <clerk-jwt>`

```bash
curl -X POST http://localhost:5001/analyze/secure \
  -H "Authorization: Bearer <clerk-jwt>" \
  -H "Content-Type: application/json" \
  -d '{"material": "def f(): pass", "filename": "x.py"}'
```

Errors: `401` missing/invalid token.

## `POST /webhook/github`

GitHub App webhook. On `pull_request` (`opened`) it analyzes the diff and posts a PR comment.

- **Auth:** `X-Hub-Signature-256` (HMAC, `GITHUB_WEBHOOK_SECRET`)

```json
{"ok": true, "triggered": true, "verdict": "REQUIRES_REVIEW"}
```

Errors: `403` invalid signature.

## `POST /webhook/stripe`

Stripe webhook. Handles `customer.subscription.updated`.

- **Auth:** `Stripe-Signature` (HMAC, `STRIPE_WEBHOOK_SECRET`)

```json
{"ok": true, "event": "customer.subscription.updated", "subscription_id": "sub_123"}
```

Errors: `400` invalid payload/signature, `500` webhook secret not set.

## `POST /billing/checkout`

Create a Stripe Checkout Session (subscription mode).

```bash
curl -X POST http://localhost:5001/billing/checkout \
  -H "Content-Type: application/json" \
  -d '{"email": "a@b.c", "success_url": "https://ok", "cancel_url": "https://cancel"}'
```

```json
{"session_id": "cs_test_...", "url": "https://checkout.stripe.com/..."}
```

## `GET /metrics`

Prometheus metrics (`text/plain; version=0.0.4`).

```bash
curl http://localhost:5001/metrics
```
