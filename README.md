[![CI](https://github.com/dvddv9/vishap/actions/workflows/ci.yml/badge.svg)](https://github.com/dvddv9/vishap/actions/workflows/ci.yml)
[![Docs](https://github.com/dvddv9/vishap/actions/workflows/docs.yml/badge.svg)](https://dvddv9.github.io/vishap/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

> рџ”¬ 6-stage LLM pipeline for analyzing engineering materials (code, spec, logs, config, data).

**Vishap** takes a file as input в†’ returns a structured Markdown report with risks, STRIDE threat model, refactoring options and **audit trail** with PII detection and compliance flags.

## рџЊђ Links

- **Documentation:** [https://dvddv9.github.io/vishap/](https://dvddv9.github.io/vishap/)
- **Landing Page:** [https://dvddv9.github.io/vishap/landing/](https://dvddv9.github.io/vishap/landing/)
- **GitHub App:** Auto-analyze PR diffs and comment on findings.
- **Releases:** [https://github.com/dvddv9/vishap/releases/latest](https://github.com/dvddv9/vishap/releases/latest)

## рџ–Ґ Desktop App (v7.0.0)

Vishap is now available as a **native desktop application** (Windows) via Tauri.

### Features
- **Native window** (3.5 MB `.exe`, 1.5 MB installer).
- **Auto-start Python backend** from `.venv`.
- **Rust IPC fallback** (bypasses Private Network Access).
- **Memory job store** (no Postgres required).
- **Clerk gated** for desktop mode.

### Download
| Platform | File |
|---|---|
| Windows (installer) | [Vishap_7.0.0_x64-setup.exe](https://github.com/dvddv9/vishap/releases/latest) |
| Windows (MSI) | [Vishap_7.0.0_x64_en-US.msi](https://github.com/dvddv9/vishap/releases/latest) |

### Quick start
1. Download `Vishap_7.0.0_x64-setup.exe`.
2. Run the installer (UAC prompt).
3. Launch **Vishap** from the Start Menu.
4. The app auto-starts the Python backend and opens the UI.

## рџљЂ What's new in v7.0.0

The slim release: one distribution, one UI, one LLM chain, one process manager.

- **Single UI surface:** Streamlit removed; `ui-next/` (and the Tauri desktop shell) is the UI.
- **Single LLM chain:** the DSH harness is the only provider. Direct DeepSeek / OpenAI / Ollama calls are gone вЂ” every stage goes through a local harness (`HARNESS_URL` + `HARNESS_TOKEN`).
- **PyPI only:** Dockerfile, compose stack, image workflows and the Docker Hub images are gone; deploy with `pip` + `systemd` ([docs/VPS-DEPLOY.md](docs/VPS-DEPLOY.md)).
- **Desktop:** Tauri app with auto-start backend, Rust IPC fallback and an in-memory job store (no Postgres).
- **Fresh history:** release tags before v7 were deleted; [docs/HISTORY.md](docs/HISTORY.md) keeps what mattered.
- **Usable UI:** copy/export the report, audit export (JSON), delete a job or clear the history, "Load example" in the analyzer, and a harness badge with a **Start** button.
- **No UAC:** the desktop app runs as a standard user (`asInvoker`) with its own per-user WebView2 profile.
- **Version:** `6.6.0` в†’ `7.0.0` everywhere.

## рџ›  Features

- **6-stage pipeline:** Ingestion в†’ Taint Analysis в†’ Dataflow в†’ Risk Assessment в†’ Verdict в†’ Report.
- **Multi-language:** Python, Java, C (AST + taint patterns).
- **Async API:** FastAPI with Celery workers.
- **Security:** HMAC-SHA256 for API keys (with pepper), Fernet for secrets.
- **Observability:** Structlog (JSON), Prometheus `/metrics`, OpenTelemetry traces.
- **CI/CD:** GitHub Actions (tests, lint, docs deploy, PyPI publish).
- **Desktop:** Tauri app (Windows).

## рџ“¦ Quick Start

### Desktop (Windows)
1. Download `Vishap_7.0.0_x64-setup.exe`.
2. Run installer (UAC).
3. Launch **Vishap** from Start Menu.

### Local dev (Windows): one-click

Double-click `start_vishap_dev.bat`. It starts the backend from `.venv` (`python -m src.main`, `PORT=8080`), starts the UI (`ui-next`, `npm run dev`, `http://localhost:3000`) and opens the browser.

### CLI (all platforms)
```bash
vishap analyze file.py
```

### API
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
python -m src.main        # http://127.0.0.1:8080/docs
```




