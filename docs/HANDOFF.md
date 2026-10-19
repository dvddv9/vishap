# HANDOFF: Vishap v6.3.0

**Дата:** 2026-10-17
**От:** senior-разработчик (сессия 3)
**Кому:** следующий senior-разработчик

## Состояние

- **Версия:** v6.3.0
- **HEAD:** fe7ceca
- **Тесты:** 553 passing (было 197)
- **Все платформы:** GitHub + PyPI + Docker Hub = 5.10.6

## 5 релизов за сессию

| Релиз | Что | Тесты |
|---|---|---|
| v5.10.2 | P2-7b AST data-flow | 213 |
| v5.10.3 | Test Suite sync | 213 |
| v5.10.4 | P2-12 Anomaly detection | 230 |
| v5.10.5 | Fix: async import + UI X-API-Key + compose env | 240 |
| v5.10.6 | Fix: risk_verdict + anomaly density | 252 |

## 6 багов dogfood

1. async_stages MAX_TOKENS_STAGE4 (v5.10.5)
2. UI missing X-API-Key (v5.10.5)
3. compose missing CONVEYOR_API_KEY (v5.10.5)
4. risk_verdict ignores risk_nodes (v5.10.6)
5. anomaly on non-numeric code (v5.10.6)
6. Test Suite stale (v5.10.3)

## Что дальше

### v5.11 -- Java/C паттерны
P2-7 regex не работает на Java/C. Добавить:
- request.getParameter, request.getHeader
- Runtime.exec, ProcessBuilder
- new File, FileInputStream

### v5.11.1 -- DONE (2026-10-15)
risk_verdict + security section -- реализовано.
- orchestrator.py: scan both risk_nodes AND security.findings

### v5.11.2 -- DONE (2026-10-15)
Refactor: consolidate risk verdict into verdict.py.
- src/pipeline/verdict.py (new): compute_risk_verdict()
- tests/test_verdict.py (new): 26 tests
- orchestrator.py: -45 lines, calls compute_risk_verdict()
- 297 passing (was 271)

### v5.11.3 -- DONE (2026-10-15)
UI api_client.py -- centralized HTTP client.
- src/ui/api_client.py (new): get()/post()/_url()
- src/config.py: +API_URL, CONVEYOR_API_KEY, API_TIMEOUT_*
- src/ui/streamlit_app.py: 8 calls refactored, removed requests/os
- tests/test_api_client.py (new): 16 tests
- tests/test_ui_headers.py: rewritten (13 tests)
- 320 passing (was 297)

### v5.11.4 -- TODO
anomaly: is_numeric_context() -- единый предикат вместо density+std-ratio guard'ов.
Оценка: 0.5 дня.

### v5.11.5 -- DONE (2026-10-15)
P2-7 Java taint patterns.
- patterns.py: TAINT_SOURCES["source_java"], TAINT_SINKS["sink_java_*"]
- patterns.py: EXPLOIT_PATTERNS["entrypoint_java_*"]
- reachability.py: _LANG_ENTRYPOINTS["java"], _is_comment_line()
- tests/test_patterns_java.py (new): 41 tests
- 361 passing (was 320)
- Dogfood: ServletSqli.java path = doGet -> getParameter -> createStatement
- Known limitation: DbConnection.java (source via method arg) -> path empty

### v5.11.6 -- DONE (2026-10-15)
P2-7 C taint patterns.
- patterns.py: TAINT_SOURCES["source_c"], TAINT_SINKS["sink_c_*"]
- patterns.py: EXPLOIT_PATTERNS["entrypoint_c_main|jni"], blast_c_*
- patterns.py: detect_exploitability -- extended blast for c_cmd/c_buffer/c_file
- reachability.py: _LANG_ENTRYPOINTS["c"], trace_taint + "c"
- tests/test_patterns_c.py (new): 35 tests
- 396 passing (was 361)
- Dogfood: c_cmd_injection.c path = main -> argv[1] -> strcpy -> system
- Known limitation: cwe122 (heap logic bug, not taint flow) -- correctly skipped

### v5.11.7 -- TODO
Java AST (P2-7b) -- JavaParser. Оценка: 2-3 дня.
Проблема: DbConnection.java (source via method arg) -> path empty.
Решение: Java AST -- аналог Python AST (dataflow.py).

### v6.0.0 -- DONE (2026-10-15)
Async API -- job-based analysis.
- src/api/jobs.py (new): in-memory job store, thread-safe
- src/main.py: POST /analyze/async, GET /status/{job_id}, GET /report/{job_id}
- BackgroundTasks -- pipeline runs in background
- tests/test_async_api.py (new): 20 tests
- 416 passing (was 396)
- Dogfood: full end-to-end (POST -> poll 42s -> report)

### v6.0.1 -- DONE (2026-10-15)
UI: async analysis, LLM mode sidebar, dataflow rendering, custom theme.
- src/ui/streamlit_app.py: header + CSS, sidebar mode, async button, dataflow expander
- tests/test_ui_async.py (new): 19 tests
- 435 passing (was 416)
- Async UI works end-to-end (34k chars, 42s)

### v6.0.2 -- DONE (2026-10-16)

Bugfix: test isolation + version test drift.

**Fixed:**
- `tests/test_ui_async.py::test_ui_has_v6_version` -- now reads version from
  `pyproject.toml` via `tomllib`, resilient to future bumps (was hardcoded
  V6.0.0, drifted at v6.0.1).
- `tests/conftest.py` -- sets `VISHAP_DATA_DIR` to a session-scoped tmp dir
  via `pytest_configure` hook, BEFORE collection. Fixes PermissionError on
  Windows: tests wrote audit files to `~/.vishap/data` (outside workspace,
  blocked by Defender / sandbox / file locks).

**Real test count:** 456 passed, 0 failed (handoff previously claimed 435).

**New test file:** `tests/test_conftest_data_dir.py` (4 tests).

**Note:** `run_tests.py` uses `subprocess.run([...])` without `env=`; it
inherits the parent env. `conftest.py` works because `pytest_configure`
runs before collection, not because env is propagated.

---

### v6.0.3 -- DONE (2026-10-16)

Refactor: JobStore abstraction (Protocol + InMemory).

**Added:**
- `src/api/job_store.py` -- `JobStore` Protocol, `Job` frozen dataclass, `JobStatus` enum.
- `src/api/job_store_memory.py` -- `InMemoryJobStore` (thread-safe via RLock).

**Changed:**
- `src/api/jobs.py` -- now a backward-compat shim. Legacy module-level API
  (create_job, get_job, update_job, delete_job, list_jobs, clear_jobs, job_count)
  delegates to a singleton `JobStore` selected via `JOB_STORE` env
  (memory | postgres; postgres -> v6.1).
- `run_tests.py` -- registered `test_job_store.py` and `test_jobs_shim_iso.py`.

**Fixed:**
- `update_job` now converts ISO-string `started_at`/`finished_at` to `datetime`.
  Production bug: `main.py` passes ISO strings; `_job_to_dict` would call
  `.isoformat()` on a `str` -> AttributeError on `/status/{job_id}`.
  Regression tests: `tests/test_jobs_shim_iso.py` (4 tests).

**Tests:**
- `tests/test_job_store.py` (new) -- 15 tests (Protocol-based).
- `tests/test_jobs_shim_iso.py` (new) -- 4 tests.
- Backward compat: `test_async_api.py` still 20/20 (main.py untouched).
- Full run: 458 passed, 0 failed.

**Foundation for v6.1:** PostgresJobStore via `JOB_STORE=postgres` env.

---

## Блочный автономный режим (v6.1+)

### Что это

Начиная с v6.1 (PostgreSQL), работаем в формате "блоков":

- Блок = большая задача (PostgresJobStore, structlog, Prometheus).
- Senior даёт ОДНУ большую инструкцию на блок.
- Harness (AI-исполнитель) выполняет автономно.
- Senior проверяет ОДИН раз в конце.

### Почему

- Меньше итераций (3-4 на v6.1 вместо 15-20).
- Harness показал надёжность (v6.0.2 + v6.0.3 — 3 бага найдены).
- Чёткие границы (DONE / BLOCKED).

### Формат инструкции блока

Senior даёт инструкцию в формате:

1. БЛОК N: <название>
2. ЦЕЛЬ: <что делаем, зачем>
3. ФАЙЛЫ: (Создать / Изменить / НЕ трогать)
4. ЗАВИСИМОСТИ (добавить в requirements.txt)
5. ШАГИ
6. ТЕСТЫ (test-first): файл + N тестов + ключевые проверки
7. КРИТЕРИЙ ГОТОВНОСТИ
8. ОГРАНИЧЕНИЯ

### Формат отчёта Harness

После блока — ОДИН отчёт:

1. Что сделано
2. Файлы (new / changed)
3. Прогоны (pytest X -v -> N passed)
4. Состояние (git status, ast.parse, cleanup)
5. Заблокировано (если есть)
6. Жду: commit (после approval senior)

### Формат BLOCKED

Если Harness не может продолжить:

1. Что не получилось
2. Что пробовал (попытки)
3. Моя гипотеза
4. Что предлагаю (варианты A/B)
5. Что НЕ трогал
6. Жду: решения от senior

### Границы (Harness НЕ делает без команды)

1. НЕ коммитит, НЕ пушит (только локально).
2. НЕ меняет существующие тесты.
3. НЕ удаляет файлы.
4. НЕ меняет архитектуру (Protocol, shim).
5. НЕ добавляет зависимости без явного списка.
6. НЕ трогает .env, docker-compose.yml (кроме указанного).
7. НЕ запускает docker push, git push.
8. Останавливается при любом риске сломать dev-среду.

### Ограничения среды (DSH sandbox)

Harness работает в песочнице DSH и НЕ может:

- Устанавливать зависимости (pip install) — нет сети.
- Запускать Docker / Postgres.
- Делать git push / docker push.
- Писать за пределами workspace.

Что делает senior (на host):

- Устанавливает зависимости.
- Запускает docker compose up / alembic upgrade.
- Integration-тесты (с живым Postgres).
- git push / docker push.

### Что делает senior после DONE

1. Review отчёта (5-10 минут).
2. Проверить ключевые файлы (git diff).
3. Убедиться, что существующие тесты не тронуты.
4. Approve -> Harness делает commit (локально).
5. Push (host).
6. Integration-тесты (host).

### История (v6.1)

- Блок 1 (PostgresJobStore): 3 BLOCKED (pip, greenlet, cleanup) -> DONE.
  16 unit + 5 integration (skipif) + 39 существующих.

---

### Блок 1 -- DONE (2026-10-16)

PostgresJobStore via SQLAlchemy 2.0 async.

**Создано:**
- src/api/job_store_postgres.py -- PostgresJobStore + JobModel (jobs table)
  - 7 async methods: create/get/update/delete/list_jobs/clear/count
  - ISO-string started_at/finished_at -> datetime in update() (v6.0.3-fix repeated)
- alembic.ini, alembic/env.py, alembic/script.py.mako, alembic/versions/001_initial_jobs.py
- tests/test_job_store_postgres.py -- 16 unit tests (mocks)
- tests/test_job_store_postgres_integration.py -- 5 integration (skipif TEST_POSTGRES_URL)

**Изменено:**
- src/api/jobs.py -- get_store() postgres branch imports PostgresJobStore
- docker-compose.yml -- add postgres:16-alpine + postgres_data volume + healthcheck
- .env.example -- add DATABASE_URL, POSTGRES_PASSWORD
- requirements.txt -- sqlalchemy[asyncio]>=2.0.30, asyncpg>=0.29.0, alembic>=1.13.0
- run_tests.py -- register test_job_store_postgres.py

**Схема БД (table jobs):**
- job_id PK (varchar(32))
- status indexed (varchar(16))
- filename (varchar(255))
- created_at, updated_at (timestamptz)
- started_at, finished_at (timestamptz, nullable)
- tenant_id indexed (varchar(64), nullable)
- result (jsonb)
- error (text)

**Тесты:**
- 16 unit passed
- 5 integration passed (с живым Postgres через docker compose + alembic upgrade head)
- Полный прогон: 478 passed + 5 skipped (integration, если нет env) + 3 e2e

**Commit:** 250155f

**Что в работе (v6.1.x):**
- RLS / multi-tenant isolation
- Prometheus /metrics (Блок 3)
- token counters + Fernet (Блок 4)

### Блок 2 -- DONE (2026-10-16)

structlog + JSON logs + Docker fixes.

**Создано:**
- src/observability/__init__.py, logging.py (setup_logging, get_logger, bind_job_id, bind_request_id, clear_context)
- tests/test_logging.py (15 тестов)

**Изменено:**
- src/config.py: LOG_LEVEL, LOG_FORMAT
- src/main.py: setup_logging + HTTP middleware log_requests
- src/api/job_store_memory.py, job_store_postgres.py: log job events
- src/pipeline/orchestrator.py: _timed_stage + stage events
- requirements.txt: +structlog>=24.0.0
- pyproject.toml: +sqlalchemy[asyncio], asyncpg, alembic, structlog (Docker fix)
- .env.example: +LOG_LEVEL, LOG_FORMAT
- run_tests.py: register test_logging.py

**Docker fixes (попутно, все запушены):**
- docker-compose.yml: vishap-ui healthcheck on 8501
- docker-compose.yml: vishap-ui volume vishap_data + VISHAP_DATA_DIR
- pyproject.toml: 4 deps для Docker pip install .
- streamlit_app.py: file_name без .md

**Тесты:**
- test_logging.py: 15 passed
- test_ui_async.py: 20 passed (+1 download test)
- На host: 494 passed (без e2e). Всего collected: 502.

**Commits:**
- 84534c5 feat(observability): structlog + JSON logs (v6.1-block2)
- 9a0ee1d fix(build): add deps to pyproject.toml
- 13f02d7 fix(docker): mount vishap_data in vishap-ui
- 8847edc fix(ui): remove .md from download_button file_name
- 0c47243 docs(readme): bump tests count 486 -> 502

**Что в работе (следующие сессии):**
- Блок 3: Prometheus /metrics (prometheus-client)
- Блок 4: token counters + Fernet

### Блок 3 -- DONE (2026-10-16)

Prometheus /metrics endpoint.

**Создано:**
- src/observability/metrics.py -- единый CollectorRegistry, 4 метрики
  (vishap_jobs_created_total, vishap_jobs_completed_total,
  vishap_job_duration_seconds, vishap_http_requests_total) + helpers.
- tests/test_metrics.py -- 12 тестов (test-first).

**Изменено:**
- src/main.py -- GET /metrics route (text/plain; version=0.0.4)
  + observe_http_request в middleware log_requests.
- src/api/job_store_memory.py -- observe_job_created + observe_job_finished
  (old != new guard).
- src/api/job_store_postgres.py -- то же (symmetry).
- requirements.txt + pyproject.toml -- prometheus-client>=0.20.0 (symmetry).
- run_tests.py -- register test_metrics.py.

**Тесты:**
- 12 new tests (metrics): endpoint, content-type, job counters,
  duration histogram, http counters, format, robustness.
- Полный прогон: 494 -> 506 passed, 5 skipped (integration).
- collected: 502 -> 514.

**Commit:** d2b7561

**Dogfood (2026-10-16):**
- Integration: 5 passed (с живым Postgres).
- /metrics: 200, text/plain; version=0.0.4.
- # HELP / # TYPE для всех 4 метрик.
- Histogram buckets: 1, 5, 10, 30, 60, 300.
- /health: ok.

**Что в работе (v6.1.x):**
- Блок 4: token counters + Fernet (secret encryption).
- RLS / multi-tenant isolation.

### Блок 4 -- DONE (2026-10-16)

LLM token metrics + Fernet encryption.

**Создано:**
- src/security/__init__.py, fernet.py -- encrypt/decrypt/generate_key/is_configured.
- src/llm/_observe.py -- DRY helper observe_llm_result.
- tests/test_fernet.py (8), test_token_metrics.py (6), test_observe.py (6).

**Изменено:**
- src/observability/metrics.py -- +2 метрики: vishap_llm_tokens_total{model, type},
  vishap_llm_requests_total{model, status}.
- src/llm/client.py + async_client.py -- обёртка observe_llm_result
  (6 + 4 вызова + error-path).
- src/config.py + .env.example -- FERNET_KEY.
- requirements.txt + pyproject.toml -- cryptography>=42.0.0 (symmetry).
- run_tests.py -- register 3 файла.

**Тесты:**
- 20 new tests (8 + 6 + 6).
- Full run (host): 531 passed (494 + 12 Block3 + 20 Block4 + 5 integration).

**Commit:** 072a288

### Block 5 -- DONE (2026-10-17)

Celery + Redis queue (production job queue).

**Создано:**
- src/api/celery_app.py -- Celery instance (broker/backend из env, acks_late, task_reject_on_worker_lost, prefetch=1) + broker_available() (TCP precheck).
- src/api/tasks.py -- run_analysis_task (@celery_app.task, bind=True, max_retries=3, default_retry_delay=30).
- tests/test_celery_app.py (4), tests/test_tasks.py (3).

**Изменено:**
- src/main.py -- /analyze/async -> run_analysis_task.delay(...) + fallback to BackgroundTasks (Redis down).
- docker-compose.yml -- redis service (redis:7-alpine, healthcheck) + worker service.
- requirements.txt + pyproject.toml -- celery[redis]>=5.3.0, redis>=5.0.0 (symmetry).
- .env.example -- CELERY_BROKER_URL, CELERY_RESULT_BACKEND.

**Тесты:** 7 new; полный 524 passed.
**Commit:** 9cef721

### Block 6 -- DONE (2026-10-17)

GitHub App (webhooks + PR auto-analyze).

**Создано:**
- src/github_app/auth.py -- generate_jwt (RS256, iat/exp=iat+600/iss=APP_ID; optional private_key param for tests).
- src/github_app/client.py -- get_installation_token, post_pr_comment, analyze_pr_diff.
- src/github_app/webhook.py -- verify_signature (HMAC SHA256) + handle_webhook (ping / pull_request opened).
- src/github_app/__init__.py -- re-exports.
- tests/test_github_auth.py (3), test_github_client.py (3), test_github_webhook.py (4).

**Изменено:**
- src/main.py -- POST /webhook/github route.
- src/config.py -- GITHUB_APP_ID, GITHUB_PRIVATE_KEY, GITHUB_WEBHOOK_SECRET.
- .env.example -- GITHUB_* placeholders.
- requirements.txt + pyproject.toml -- PyJWT>=2.9.0 (symmetry).
- run_tests.py -- register 3 files.

**Тесты:** 10 new; полный 535 passed.
**Commit:** 7a4e453

**Known limitation:** webhook синхронно вызывает analyze_pr_diff (production -> Celery.delay, TODO).

### Block 7 -- DONE (2026-10-17)

Clerk JWT auth (multi-tenant, SSO-ready).

**Создано:**
- src/auth/clerk.py -- AuthError + verify_jwt (RS256, JWKS cache, kid/sub checks, separate errors for expired/invalid signature).
- src/auth/middleware.py -- current_user dependency (Authorization: Bearer <jwt> -> {user_id, claims}; 401 on missing/invalid).
- src/auth/__init__.py -- re-exports.
- tests/test_auth_clerk.py (4), test_auth_middleware.py (3).

**Изменено:**
- src/main.py -- POST /analyze/secure (dependency current_user); /analyze (API key) untouched.
- src/config.py -- CLERK_SECRET_KEY, CLERK_JWKS_URL.
- .env.example -- CLERK_* placeholders.
- run_tests.py -- register 2 files.

**Тесты:** 7 new; полный 542 passed.
**Commit:** a2f3e1d

### Block 8 -- DONE (2026-10-17)

Stripe billing (subscriptions + webhook + usage).

**Создано:**
- src/billing/stripe_client.py -- BillingError, _stripe() lazy init, create_checkout_session, get_customer, record_usage(customer_id, quantity) via Billing Meters API (stripe>=16 removed SubscriptionItem.create_usage_record).
- src/billing/webhook.py -- handle_stripe_webhook (construct_event + stripe.SignatureVerificationError; dispatch customer.subscription.updated -> subscription_id).
- src/billing/__init__.py -- re-exports.
- tests/test_stripe_client.py (3), test_billing_webhook.py (3).

**Изменено:**
- src/main.py -- POST /billing/checkout + POST /webhook/stripe.
- src/config.py -- STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID.
- .env.example -- STRIPE_* placeholders + STRIPE_METER_EVENT (optional).
- requirements.txt + pyproject.toml -- stripe>=10.0.0 (symmetry).
- run_tests.py -- register 2 files.

**Тесты:** 6 new; полный 548 passed.
**Commit:** 8ac77a0

### Block 9 -- DONE (2026-10-17)

Docs Docusaurus (site + GitHub Pages deploy).

**Создано:**
- docs-site/ (Docusaurus classic, TS): 5 pages (getting-started, api-reference, cli, architecture, case-studies)
- .github/workflows/docs.yml (build -> deploy GitHub Pages)

**Изменено:**
- README.md: Documentation section.
- .gitignore: node_modules/build/.docusaurus ignored.

**Тесты:** (не требует, статичный сайт). Build + Deploy OK.
**Commit:** 8564f46

### Block 10 -- DONE (2026-10-17)

### Block 11 -- DONE (2026-10-17)

Observability: OpenTelemetry + Tempo + Prometheus + Grafana.

**Создано:**
- src/observability/tracing.py (fail-open OTel wrapper).
- docker/tempo/tempo.yaml (local storage, OTLP http/grpc).
- docker/prometheus/prometheus.yml (scrape API).
- docker/grafana/provisioning/ (datasources + dashboards).
- tests/test_tracing.py (5 tests).

**Изменено:**
- src/main.py, src/pipeline/orchestrator.py, src/api/tasks.py (spans).
- docker-compose.yml: tempo (:3200/:4318/:4317), grafana (:3001), prometheus (:9090).
- .env.example: OTEL_* vars.

**Тесты:** 553 passed. Traces OK (Tempo API). Metrics OK (Prometheus /metrics).

**Commit:** 3dc7a54 + a763804 (Prometheus fix) + f564563 (vishap.yml non-blocking).

### Block 12 -- DONE (2026-10-17)

PyPI Trusted Publishing (GitHub Actions OIDC).

**Создано:**
- .github/workflows/publish.yml (build + twine check + pypa/gh-action-pypi-publish, OIDC).

**Изменено:**
- pyproject.toml: version 6.2.1, name "vishap-analyzer".
- src/version.py, src/ui/streamlit_app.py: sync version.

**Тесты:** N/A (CI publish). Published to PyPI (v6.2.1, v6.3.0).

**Commit:** 0a1054f (publish.yml), 37afcf5 (v6.2.1).

### Block 13 -- DONE (2026-10-17)

UI Next.js Dashboard (Clerk + Tailwind).

**Создано:**
- ui-next/ (Next.js 16, App Router, TS, Tailwind 4).
- src/lib/api.ts, types.ts (typed API client).
- src/proxy.ts (Clerk middleware, Next 16 convention).
- src/app/page.tsx, analyze/page.tsx, report/[id]/page.tsx.
- src/components/Navbar.tsx, JobCard.tsx, UploadForm.tsx.

**Изменено:**
- README.md: UI docs.

**Тесты:** npm run build OK (3 routes). 553 Python tests passed.

**Ограничение:** Next.js 16 requires Suspense for usePathname/useParams (cacheComponents). Fixed.

**Commit:** fe7ceca.

### Block 14 -- DONE (2026-10-17)

Fix CI: `vishap.yml` (dogfood) non-blocking.

**Изменено:**
- .github/workflows/vishap.yml: `continue-on-error: true` on Quality Gate (Ollama unavailable in GitHub runner).

**Причина:** Vishap requires live Ollama for LLM analysis. CI runner doesn't have Ollama (no GPU/RAM). Non-blocking -> workflow green.

**Commit:** f564563.


Landing page (static HTML + Tailwind CDN).

**Создано:**
- docs-site/static/landing/index.html (6 sections: hero, features, pricing, cta, etc.)
- docs-site/static/landing/assets/style.css + script.js
- docs-site/static/landing/favicon.ico

**Изменено:**
- README.md: landing URL.
- **GitHub Pages enabled** (repo -> public, Source -> GitHub Actions).

**Тесты:** (статичный сайт). Build + Deploy OK.
**Commit:** 0b8230c



**Dogfood (2026-10-16):**
- Fernet: roundtrip OK, type=bytes, len=100, non-deterministic.
- Integration: 5 passed (Postgres).
- Docker: 3 healthy.

**Что в работе (v6.1.x):**
- RLS / multi-tenant isolation.
- CI (GitHub Actions) -- не настроен.



### Block 16 -- DONE (2026-10-17)

Multi-tenant RLS (Row-Level Security) — production-ready.

**Создано:**
- alembic/versions/002_add_rls_jobs.py (RLS policy + role vishap_app + index).
- alembic/versions/003_force_rls.py (FORCE ROW LEVEL SECURITY).
- tests/test_rls.py (25 tests).

**Изменено:**
- src/api/job_store.py (async Protocol + ContextVar).
- src/api/job_store_memory.py (async + tenant scoping).
- src/api/jobs.py (async-ядро + sync-фасад).
- src/api/tasks.py (Celery tenant + asyncio.run).
- src/main.py (/status, /report — tenant_scope).
- src/auth/middleware.py (current_tenant).
- tests/test_job_store.py, test_jobs_shim_iso.py, test_logging.py, test_metrics.py (async).

**Тесты:** 583 passed (0 failed, 2 skipped для суперюзера).
**RLS verified:** под vishap_app — 25 passed (0 skipped).

**Грабли:** #24 (RLS не применяется к суперюзерам — для production использовать vishap_app).

**Commit:** 61e4fd0 + 5fc205a (merge) + d056bd6 + 8105de8.

### Block 16.1 -- DONE (2026-10-17)

History + FORCE RLS.

**Создано:**
- tests/test_history.py (6 tests).

**Изменено:**
- src/storage/history.py (add_entry + load_history с tenant_id).
- src/main.py (/history, /history/clear — tenant_scope).

**Тесты:** 583 passed (+6 history).
**Commit:** d056bd6 + 8105de8.

### v6.1 -- TODO
PostgreSQL + Observability + Security. Оценка: 1 неделя.
- Replace in-memory job store with PostgreSQL
- Multi-tenant schema (tenant_id)
- Structured logging + token counters
- /metrics endpoint (Prometheus)
- Secret encryption

### v6.2 -- TODO
UI (Next.js) [DONE in Block 13]. Оценка: 1.5 недели.

### v6.3 -- TODO
GitHub App [DONE Block 6] + Billing (Stripe) [DONE Block 8]. Оценка: 1 неделя.

### v5.11.7 -- TODO (deferred)
Java AST (P2-7b) via javalang. Оценка: 2-3 дня.

### v5.11.4 -- TODO
anomaly: is_numeric_context() -- единый предикат вместо density+std-ratio guard'ов.
Оценка: 0.5 дня.

### v5.11.5 -- TODO
Java/C patterns для P2-7 (regex). Оценка: 2-3 дня.
### v6.0 -- React UI + Multi-tenant
Streamlit заменить на React. 1-2 недели.

## Грабли (10-21)

10. Anchor без отступа -> IndentationError. ВСЕГДА ast.parse сразу.
11. Не копировать git diff в консоль (PowerShell выполнит).
12. docker compose up -d не пересоздаёт. Нужен --force-recreate.
13. ,, двойная запятая в regex-патче.
14. "test_X.py" in src != в таблице. Проверять точный формат.
15. \\n в heredoc строке -> SyntaxError. Использовать конкатенацию.
16. Inline python -c в PowerShell съедает кавычки. Всегда через .py файл.
17. Get-Content .env в чат -> ключи утекли. Только имена:
    (Get-Content .env | Select-String "^KEY=").Line -replace "^KEY=".
18. PowerShell here-string @"..."@ НЕ обрабатывает \" escape.
    В here-string кавычки пишутся как есть.
19. Out-File -Encoding utf8 (PS 5.1) добавляет BOM.
    Через [System.IO.File]::WriteAllText($path, $msg,
    (New-Object System.Text.UTF8Encoding $false)).
20. GitHub UI переводит контент при русском языке профиля.
    Settings -> Appearance -> Language -> English (обязательно).
21. Copilot review может найти реальные фактические проблемы.
    Проверять факт (curl.se/download) -- не игнорировать, не спорить.

22. Review по фрагменту файла из чата -- ложный баг. Фрагмент может обрезать
    верхние import. ВСЕГДА запрашивать Get-Content целиком (или первые 10 строк)
    перед claim'ом «нет import».

23. GitHub Pages 404: если репозиторий Private, Pages недоступен (бесплатный план).
    Deploy action падает с HttpError 404. Фикс: Settings -> General -> Change to Public,
    затем Settings -> Pages -> Source: GitHub Actions.

24. RLS не применяется к суперпользователям (vishap в Docker -- superuser).
    Даже FORCE ROW LEVEL SECURITY не действует: суперюзер и роли с BYPASSRLS
    обходят политики. Для production -- отдельная роль vishap_app
    (не суперюзер и не owner) в DATABASE_URL. Integration-тесты в
    tests/test_rls.py скипаются, если current_setting('is_superuser') = 'on'
    или у роли rolbypassrls = true.



## Что осталось (TODO) — на 2026-10-18

### P1 (Продукт) — блокеры для enterprise-продаж

| # | Задача | Размер | Приоритет |
|---|---|---|---|
| 1 | **Enterprise invoices (Stripe)** — Invoicing API (ручной биллинг для enterprise). | 1-2 дня | P1 |
| 2 | **`/api/me/data` (GDPR)** — экспорт/удаление данных пользователя. | 1 день | P1 |
| 3 | **SSO (SAML)** — Clerk Enterprise plan ($25/мес) или WorkOS. | 2-3 дня | P1 |

### P2 (Рост) — маркетинг и distribution

| # | Задача | Размер | Приоритет |
|---|---|---|---|
| 4 | **GitHub Marketplace** — публикация GitHub App (review ~1 неделя). | 1 неделя | P2 |
| 5 | **Blog + changelog** — Docusaurus blog (auto from GitHub Releases). | 1 день | P2 |
| 6 | **AWS Marketplace** — только после 10+ enterprise-клиентов (3-6 мес). | 3-6 мес | P3 |

### P3 (Enterprise) — сертификации

| # | Задача | Размер | Приоритет |
|---|---|---|---|
| 7 | **SOC 2** — аудит (Vanta/Drata, $10-20k/год). | 6-12 мес | P3 |
| 8 | **ISO 27001** — аудит (€15-30k). | 6-12 мес | P3 |
| 9 | **HIPAA** — BAA + аудит (только если медицина). | 3-6 мес | P3 |
| 10 | **Pen-test** — ежегодный (€5-15k). | 2-4 недели | P3 |

### P0 (Баги / Tech Debt) — если найдутся

| # | Задача | Приоритет |
|---|---|---|
| 11 | **`vishap.yml` (dogfood)** — non-blocking (Ollama unavailable in CI). **Сделано** (f564563). | — |
| 12 | **`/history` (cross-tenant)** — **Сделано** (Block 16.1). | — |
| 13 | **FORCE RLS** — **Сделано** (Block 16.1, миграция 003). | — |
| 14 | **Аудит export (CSV/JSON)** — **Сделано** (Block 17). | — |

### P4 (Nice-to-have) — для полноты

| # | Задача | Размер |
|---|---|---|
| 15 | **Java AST (v5.11.7)** — javalang (deferred, 2-3 дня). | 2-3 дня |
| 16 | **OTel для Celery** — span для `celery.run_analysis` (уже есть, но можно расширить). | 0.5 дня |
| 17 | **RLS для `audit` таблицы** (если появится). | 1 день |
| 18 | **CI: Docker push** — автоматическая сборка образа в GitHub Actions. | 1 день |

### Что сделано (для контекста)

- ✅ **Block 16:** RLS (multi-tenant) + FORCE RLS.
- ✅ **Block 16.1:** History + FORCE RLS.
- ✅ **Block 17:** Audit export (CSV/JSON).
- ✅ **Block 18:** Case Study #1 (cookie.c).
- ✅ **Block 18.1:** Case Study #2 (http2.c).
- ✅ **Block 18.2:** Full Reports.
- ✅ **Block 18.3:** Cleanup + version alignment.

### Рекомендуемый порядок (следующая сессия)

1. **Enterprise invoices (P1)** — 1-2 дня (быстро, разблокирует enterprise).
2. **`/api/me/data` (GDPR, P1)** — 1 день (compliance).
3. **SSO (SAML, P1)** — 2-3 дня (enterprise).
4. **GitHub Marketplace (P2)** — 1 неделя (distribution).
5. **SOC 2 / ISO 27001 (P3)** — когда будет 10+ enterprise-запросов.

## Ключи

Ротированы 2026-10-14:
- DeepSeek: .env
- PyPI: ~/.pypirc
- Docker Hub: docker login -u dvddv9

## Запуск

    cd C:\AI\conveyor_app
    .\.venv\Scripts\Activate.ps1
    python run_tests.py
    python -m src.cli analyze file.py
    python -m src.main
    docker compose up -d

## Harness (DSH) integration (2026-10-17)

Vishap may use DeepSeek Harness (DSH) as an LLM provider - agent with
workspace access (files, shell, multi-turn), not just a chat response.

**Commits:**
- `9523f14` - feat(llm): add Harness (DSH) provider
- `caf45e9` - feat(llm): expose Harness mode via UI + mode API
- `48004bd` - feat(llm): full Harness integration - sync + async
- `d244c1c` - docs: add HARNESS.md

**Architecture:**
- `src/llm/harness_client.py` - sync client (Typert RPC over HTTP + JSONL log read via zstandard).
- `src/llm/client.py` - `harness` branch in `chat()` (sync).
- `src/llm/async_client.py` - `harness` branch in `async_chat()`, wraps sync client in `loop.run_in_executor`.
- `src/storage/mode.py` - `harness` in `VALID_MODES`.
- `src/ui/streamlit_app.py` - sidebar option Harness (DSH).

**Config (.env):**
```
HARNESS_URL=http://127.0.0.1:3080
HARNESS_TOKEN=<from dsh web>
VISHAP_LLM_PROVIDER=auto
VISHAP_DATA_DIR=C:\AI\conveyor_app\data
```

**Docs:** `docs/HARNESS.md` (setup, switching, troubleshooting).

**Known limitation:**
- No fallback (DSH down -> 500). Recommended next session.
- DSH developer preview; RPC + log format may change.
- `session.v4.jsonl.zstd` filename versioned.

**Tests:** none yet. Recommended: `tests/test_harness_client.py`
(mock httpx + zstandard).

## Case study

docs/case-studies/dogfood/RequestFilter-java/
- Реальный Sakai Java код.
- D3, $0.008, 11 risk_nodes (3 critical).
- Триггер для v5.10.5 + v5.10.6.

## Curl PR #23441 (2026-10-16)

Docs: encourage verifying tarball before unpacking.

**История:**
- Issue #23438 -- closed by Daniel Stenberg after AI-slop complaint.
- Second chance via human reply -> PR accepted.
- PR: https://github.com/curl/curl/pull/23441

**Status:**
- Open, awaiting CI approval (first-time contributor, 5 workflows pending).
- Label: `documentation` (auto).
- Files: docs/INSTALL.md, +17.
- Commit: a8aefa1 (no BOM).

**Обновление (2026-10-16, позже):**
- CI: 13/13 success на head 68e6d27.
- Copilot review: finding про sha256sum (curl не публикует .sha256) -- ИСПРАВЛЕНО.
- HEAD SHA: 68e6d27 (был a8aefa1).
- Status: waiting for human review.
- Наш ответ Copilot: "The download page currently publishes only .asc (GPG),
  not .sha256. I removed the sha256sum example."

**Что делать:**
- НЕ комментировать в issue #23438.
- НЕ пинговать Daniel/Stefan.
- Ждать 7 дней. Если тишина -> один вежливый ping в PR.

**LESSONS.md:** записан.

## Философия

1. Dogfood на каждой фиче.
2. Test-first.
3. Идемпотентные патчи (SKIP не ERROR).
4. Fail-open для новых фич.
5. Не копить расхождение платформ.
6. Case study на сложных кейсах.

Удачи! 252 теста -- не сломай.

## Сессия 2026-10-18 (v6.5.0)

### DONE
- RLS, Audit export, Case Studies, P1, P2, Deploy, Manual Billing
- v6.5.0 release (PyPI + Docker Hub)

### TODO
- [x] sha256(key) (P0) — v6.5: HMAC-SHA256 keyed with `API_KEY_PEPPER`; keys issued
      before the pepper (plain sha256) are accepted once and rehashed on use.
      `API_KEY_PEPPER` is required at runtime; changing it invalidates every
      issued key, so rotate deliberately.
- [x] SMTP (P1) — v6.5: `src/notifications/email.py` sends over SMTP when
      `SMTP_HOST`/`SMTP_USER`/`SMTP_PASSWORD` are set, and is a no-op returning
      `False` otherwise.
- [x] Save Reports (P1) — v6.5: `data/reports/<job_id>.md` plus
      `GET /report/{job_id}/download` (falls back to the job result when the file
      is missing).
- VPS (P0) — `docs/VPS-DEPLOY.md` written; the automated deploy workflow is
      disabled, deployment is manual for now.
- Stripe Live (P0) — `docs/STRIPE-LIVE.md` written; live keys, live price and the
      live webhook are not configured yet.

