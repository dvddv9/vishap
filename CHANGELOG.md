# Changelog

All notable changes to Vishap. Format based on [Keep a Changelog](https://keepachangelog.com/).

---

## [6.0.1] - 2026-10-15

### Added

- **UI: async analysis, LLM mode sidebar, dataflow rendering.**
  - Custom header (🐉 gradient) + CSS theme.
  - Sidebar: LLM mode selector (`auto` / `cloud` / `local`).
  - `⚡ Async` button -- non-blocking analysis via async API.
  - Dataflow expander -- shows `dataflow_path` for Java/C.

### Tests

- `tests/test_ui_async.py` (new) -- 19 tests.
- 435 passing (was 416).

## [6.0.0] - 2026-10-15

### Added

- **Async API -- job-based analysis.**
  - `src/api/jobs.py` (new) -- in-memory job store, thread-safe.
  - `POST /analyze/async` -- returns `{job_id, status: "queued"}` immediately.
  - `GET /status/{job_id}` -- poll job status.
  - `GET /report/{job_id}` -- fetch result (409 if not done).
  - `BackgroundTasks` -- pipeline runs in background.
  - Sync `/analyze` unchanged (backward compatible).

### Tests

- `tests/test_async_api.py` (new) -- 20 tests.
- 416 passing (was 396).

### Dogfood

- Full end-to-end: POST -> job_id -> poll (42s) -> report with stages 0-4 + audit.

## [5.11.6] - 2026-10-15

### Added

- **P2-7: C taint patterns (regex-based data flow).**
  - `TAINT_SOURCES["source_c"]` -- scanf/fgets/gets/read/recv, argv[], getenv.
  - `TAINT_SINKS["sink_c_cmd|buffer|file"]` -- cmd, buffer, file.
  - `EXPLOIT_PATTERNS["entrypoint_c_main|jni"]`, `blast_c_cmd|buffer|file`.
  - `_LANG_ENTRYPOINTS["c"]` -- C entry points mapping.
  - `trace_taint` auto-detects C.
  - Blast radius logic extended for C: `c_cmd` -> high, `c_buffer` -> medium, `c_file` -> low.

### Tests

- `tests/test_patterns_c.py` (new) -- 35 tests.
- 396 passing (was 361).

### Dogfood

- `examples/own/c_cmd_injection.c` (new) -- path `main -> argv[1] -> strcpy -> system`, blast_radius: high.

## [5.11.5] - 2026-10-15

### Added

- **P2-7: Java taint patterns (regex-based data flow).**
  - `TAINT_SOURCES["source_java"]` -- Servlet/Spring/System/IO sources.
  - `TAINT_SINKS["sink_java_sql|cmd|file|reflect|deser|jndi"]` -- SQL, cmd, file, reflection, deserialization, JNDI (Log4Shell).
  - `EXPLOIT_PATTERNS["entrypoint_java_main|spring|servlet"]` -- main, Spring annotations, Servlet doGet/doPost.
  - `_LANG_ENTRYPOINTS["java"]` -- entry points mapping.
  - `trace_taint` auto-detects Java; comment lines skipped.

### Tests

- `tests/test_patterns_java.py` (new) -- 41 tests.
- 361 passing (was 320).

### Dogfood

- `examples/own/ServletSqli.java` (new) -- path `doGet -> getParameter -> createStatement`.
- Known limitation: `DbConnection.java` path is empty (source via method argument, no AST for Java).

## [5.11.3] - 2026-10-15

### Changed

- **Refactor: UI api_client.py** -- `streamlit_app.py` had 8 duplicated `requests.*` calls with manual `headers=HEADERS`. Headers defined in 3 places.
  - New module: `src/ui/api_client.py` -- `get()`, `post()`, `_url()` with auto headers + timeouts.
  - `src/config.py`: added `API_URL`, `CONVEYOR_API_KEY`, `API_TIMEOUT_*`.
  - `src/ui/streamlit_app.py`: 8 calls refactored, local `API_URL`/`API_KEY`/`HEADERS` removed.

### Added

- `tests/test_api_client.py` -- 16 tests (mocked HTTP).
- `tests/test_ui_headers.py` -- rewritten: 13 tests (now checks `api_client` and absence of direct `requests.*` in UI).

### Tests

- 320 passing (was 297).

## [5.11.2] - 2026-10-15

### Changed

- **Refactor: consolidated risk verdict computation** -- `run_audit()` had ~45 lines of inline verdict logic (v5.10.6 + v5.11.1) with duplicated `critique` / `risk_verdict` branches.
  - New module: `src/pipeline/verdict.py`.
  - Function: `compute_risk_verdict(stage2_result, pii, compliance, cwe_ids, force_emergency) -> (risk_verdict, critique_verdict)`.
  - Priority order: emergency > pii/compliance/cwe > critical risk_nodes > critical security.findings > SAFE.

### Fixed

- `critique_verdict` now correctly returns `EMERGENCY` on force_emergency (was `SAFE` -- inconsistent with `risk_verdict`).

### Added

- `tests/test_verdict.py` -- 26 tests.

### Tests

- 297 passing (was 271).

## [5.11.1] - 2026-10-15

### Fixed

- **risk_verdict ignored stage2.security.findings** -- `run_audit()` only checked `stage2.risk_nodes` (v5.10.6), ignoring `stage2.security.findings`. A file with critical `SEC-N` but no critical `RN-N` got a false `SAFE`. Fix: scan both `risk_nodes` and `security.findings` for critical priority.

### Added

- `tests/test_risk_verdict_security.py` -- 8 regression tests.

### Tests

- 271 passing (was 263).

## [5.7.1] - 2026-10-12

### Fixed (review + dogfood P0)

- **material_hash collisions** — context (filename + session_id) added to hash input (`ce3953d`)
- **PII redaction before LLM** — 15 regex patterns, placeholders (`<EMAIL_REDACTED>`) before cloud send (`7b23c24`)
- **LLM HTTP timeout** — 60s + tenacity retry with exponential backoff (`9063927`)
- **API auth + rate limit** — X-API-Key + 10/min limiter + CORS + 127.0.0.1 fallback (`fbfb48f`)
- **EMERGENCY-downgrade gate** — CRITICAL_RISK_PATTERNS (RCE, SQLi, path traversal, XXE, SSTI, LDAPi) (`48dddd0`)
- **[AUDIT_TRAIL] dedup** — strip_llm_audit_blocks from LLM output (`2000501`)
- **material_hash_full** — SHA-256 of original (before truncation) (`8ca7f4e`)
- **material_complete** — deterministic `not truncated` (`9459a53`)
- **risk_verdict** — separated from critique_verdict (`e500c80`)
- **emergency path UnboundLocalError** — fixed (`e500c80`)
- **748 material_hash places** — all 64-hex or LEGACY (`71af15f`, `0e68b05`, `08ce35d`)

### Added

- **PROOF.md** — 13 evidence sections (`e6d3829`, `0e68b05`)
- **FINDINGS.md** — dogfood findings, 5 P0 bugs (`a5b444f`)
- **8 dogfood reports** — code, config, spec, data (`27aabb4`)
- **STONESOUP CWE-129B** — SARD case study (`a48b228`)
- **deployment/** — Dockerfile, docker-compose, systemd, .env.example (`003f9a8`)
- **SECURITY.md** — threat model + controls + honest boundaries (`7929f1e`)
- **docs/LIMITATIONS.md** — 10 honest boundaries (`ce7cf19`)
- **docs/FAQ.md** — 10 common questions (`acba0af`)
- **src/api/auth.py** — X-API-Key dependency
- **src/api/rate_limit.py** — in-memory sliding window
- **src/tools/redact.py** — pre-LLM redaction
- **src/tools/patterns.py** — PII_PATTERNS + CRITICAL_RISK_PATTERNS

### Changed

- `compute_hash` — added `context` param
- `run_audit` — added `force_emergency`, `context`, `redaction_map` params
- `AnalyzeResponse` — added `audit`, `completeness`, `material_hash_full`, `truncated`, `original_size`
- `run_pipeline` — redaction before Stage 0
- `uvicorn.run` — dynamic host (127.0.0.1 if no API key)

### Security

- API key from `VISHAP_API_KEY` env var
- CORS restricted to `localhost:8501`
- Rate limit 10/min for /analyze
- PII/secrets redacted before cloud LLM

---

## [5.7.0] - 2026-10-08

### Added

- **6-stage LLM pipeline** — Orchestrator, Scanner, Analyst, Researcher, Synthesizer, Transmitter
- **Multi-material** — code (.py, .go, .js, .ts, .java, .rs), spec (.md), logs (.txt), config (.yaml, .json), data (.json)
- **Audit trail** — SHA-256 material_hash, pii_detected, compliance_flags, critique_verdict
- **EMERGENCY interrupt** — Stage 0 stops pipeline on critical risk
- **FastAPI API** — /analyze, /analyze/batch, /history, /mode, /health
- **Streamlit UI** — file upload, history, download markdown
- **DeepSeek cloud** + **Ollama local** fallback
- **41 tests** — PII, compliance, JSON, pipeline mock, e2e
- **39 case studies** — FastAPI, Django, Flask, Express, Go stdlib, Log4Shell, OpenSSL, Redis, K8s, PostgreSQL, Juice Shop, DVGA, RailsGoat, DVWA, TerraGoat
- **CI** — GitHub Actions, py3.11 + py3.12

### Known limitations

- Truncation at 12 000 chars
- LLM-based (may produce false positives)
- No SAST/SCA integration
- No SARIF output
- No formal threat model (added in 5.7.1)

---

[5.7.1]: https://github.com/dvddv9/vishap/compare/v5.7.0...v5.7.1
[5.7.0]: https://github.com/dvddv9/vishap/releases/tag/v5.7.0

*Vishap V5.8 - production-ready.*