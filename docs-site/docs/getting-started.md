# Getting Started

Vishap is a 6-stage LLM pipeline that analyzes code, config, specs, logs, and data, and returns a structured Markdown report with risks, a STRIDE threat model, refactoring options, and an audit trail (SHA-256, PII detection, compliance flags, provenance).

## Prerequisites

- Python 3.11 or 3.12
- A running DSH harness and its token (`HARNESS_URL`, `HARNESS_TOKEN`) — the only LLM provider

## Install

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your keys.

## Quick start

### CLI

```bash
vishap analyze path/to/file.py
```

### API

```bash
python -m src.main
# -> http://localhost:5001/docs
```

```bash
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"material": "def f(): pass", "filename": "x.py"}'
```

### Async (Celery + Redis)

```bash
# Redis must be running: apt install redis-server, or any managed instance
celery -A src.api.celery_app worker --loglevel=info

curl -X POST http://localhost:5001/analyze/async \
  -H "Content-Type: application/json" \
  -d '{"material": "def f(): pass", "filename": "x.py"}'
# -> {"job_id": "...", "status": "queued"}

curl http://localhost:5001/status/<job_id>
curl http://localhost:5001/report/<job_id>
```

## Next steps

- [Architecture](./architecture)
- [API Reference](./api-reference)
- [CLI](./cli)
- [Case Studies](./case-studies)
