# Vishap

[![CI](https://github.com/dvddv9/vishap/actions/workflows/ci.yml/badge.svg)](https://github.com/dvddv9/vishap/actions/workflows/ci.yml)
[![Docs](https://github.com/dvddv9/vishap/actions/workflows/docs.yml/badge.svg)](https://dvddv9.github.io/vishap/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

> 🐉 **Vishap** — 6-stage LLM pipeline for analyzing engineering materials (code, spec, logs, config, data).

**Vishap** takes a file as input → returns a structured Markdown report with risks, STRIDE threat model, refactoring options and **audit trail** with PII detection and compliance flags.

## 🌐 Links

- **Documentation:** https://dvddv9.github.io/vishap/
- **Landing Page:** https://dvddv9.github.io/vishap/landing/
- **GitHub App:** Auto-analyze PR diffs and comment on findings.
- **Releases:** https://github.com/dvddv9/vishap/releases/latest

## 🎉 What's new in v7.2.0

- **Direct DeepSeek API**: removed the DSH harness dependency. Vishap now talks to DeepSeek directly via `DEEPSEEK_API_KEY`, simplifying the architecture and reducing startup time.
- **Multi-provider UI**: switch between **Custom (OpenAI-compatible)**, **Harness (DSH)**, and **DeepSeek (direct)** right from the Dashboard. Settings are persisted in `data/settings.json` and applied immediately.
- **Local setup automation**: `install.bat`, `start_all.ps1`, `create_shortcut.ps1`, `apply_custom_llm.py` — one-click launch on Windows, desktop shortcut, BOM fixes, and a ready-made OpenAI-compatible provider.
- **Database & history**: full PostgreSQL 16 support with Alembic migrations (`001`–`005`) for persistent jobs, tenants, and audit trails.
- **Improved analysis**: validated the 6-stage pipeline on real-world materials (TOCTOU, RCE via `exec`, symlink escapes, STRIDE threat modelling with 24 threats).

## 🛠️ Features

- **6-stage pipeline:** Ingestion → Taint Analysis → Dataflow → Risk Assessment → Verdict → Report.
- **Multi-language:** Python, Java, C (AST + taint patterns).
- **Multi-provider LLM:** DeepSeek (direct), DSH Harness, or any OpenAI-compatible endpoint (Groq, OpenAI, Mistral, OpenRouter, Together).
- **Async API:** FastAPI + Celery workers (optional in-process fallback).
- **Security:** HMAC-SHA256 for API keys (with pepper), Fernet for secrets.
- **Observability:** Structlog (JSON), Prometheus `/metrics`, OpenTelemetry traces.
- **CI/CD:** GitHub Actions (tests, lint, docs deploy).
- **Desktop:** Tauri app for Windows.

## 📦 Quick Start (Windows)

### One-click installer
1. Download the repo (ZIP or `git clone`).
2. Double-click `install.bat`.
3. Wait for it to install Python, Node.js, PostgreSQL, and dependencies.
4. Double-click `start_all.ps1` (or the **Vishap** desktop shortcut) — the API, UI, and DSH (if needed) will start and the browser will open.

### Manual API + UI
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.main        # http://127.0.0.1:8080/docs

# in a second window
cd ui-next
npm install
npm run dev               # http://localhost:3000