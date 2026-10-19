# Roadmap — Vishap

**Куда идёт проект. Что отложено и почему.**

---

## v5.8 — 2026-10-12 (текущий)

**Статус:** production-ready.

**Сделано:**
- 10/10 review (audit, hash, API, risk_verdict)
- 5/5 dogfood P0 (hash collisions, PII redaction, LLM timeout, API auth, EMERGENCY gate)
- deployment/ (systemd unit, deploy notes)
- SECURITY.md, LIMITATIONS.md, FAQ.md, CHANGELOG.md
- PROOF.md (13 доказательств)
- STONESOUP CWE-129B case study
- 748 material_hash → 64-hex

---

## v5.8 — Q1 2027

**Фокус:** IT-интеграция + CI-ready.

### P1 — важно

- [ ] **SARIF output** — стандартный формат для GitHub Code Scanning
- [ ] **OWASP Top 10 mapping** — CWE → OWASP (A03:2025 Injection для CWE-89)
- [ ] **SAST integration** — Bandit (Python), gosec (Go), Semgrep (multi) до LLM
- [ ] **SCA integration** — pip-audit, npm audit, govulncheck
- [ ] **Secret pre-commit hook** — gitleaks/TruffleHog до коммита
- [ ] **Provenance block** — source, commit, author, date в Metadata

### P2 — желательно

- [ ] **Compliance mapping** — PCI-DSS Req 6.5.1, GDPR Art. 32
- [ ] **API contract review** — OpenAPI, GraphQL
- [ ] **Runbook generation** — шаги при инциденте
- [ ] **Exploitability section** — reachability, blast radius, exploit path

---

## v6.0 — Q2-Q3 2027

**Фокус:** Enterprise features.

### Product

- [ ] **Multi-tenant** — организации, роли, RBAC
- [ ] **Webhook CI integration** — GitHub App, GitLab CI
- [ ] **REST API v2** — async jobs, streaming
- [ ] **Dashboard** — metrics, trends, MTTR
- [ ] **Slack/Teams integration** — alerts

### LLM

- [ ] **Multi-model** — выбор модели per stage
- [ ] **Fine-tuning** — на собственных SARD-кейсах
- [ ] **Prompt caching** — снижение стоимости на 50%+
- [ ] **Streaming** — progressive output

### Security

- [ ] **Sandbox** — изоляция LLM (Firecracker, gVisor)
- [ ] **Prompt injection detection** — семантический
- [ ] **Full PII redaction** — Presidio integration
- [ ] **Audit log encryption** — at-rest

---

## v6.1+ — 2028

**Фокус:** Расширение домена.

- [ ] **Compliance certifications** — SOC2, ISO 27001
- [ ] **Enterprise SSO** — SAML, OIDC
- [ ] **On-prem air-gapped** — без интернета
- [ ] **Multi-language plugins** — Kotlin, Swift, PHP
- [ ] **K8s operator** — auto-scaling, HA

---

## Отложено (и почему)

### 1. Real-time analysis

**Почему отложено:** LLM latency 40-90 сек. Для real-time нужна другая архитектура.

**Когда:** v6.1+ (если будет спрос).

### 2. Custom fine-tuning

**Почему отложено:** требует большого датасета SARD-кейсов + GPU. Дорого.

**Когда:** v6.0 (если будет финансирование).

### 3. Mobile app

**Почему отложено:** Vishap - для разработчиков. Mobile не приоритет.

**Когда:** Никогда (нет use case).

### 4. Closed-source enterprise edition

**Почему отложено:** AGPL не позволяет closed-source. Если нужна enterprise — нужна другая лицензия (dual licensing).

**Когда:** v6.0 (если будет спрос).

---

## Non-goals (не делаем)

- **Не** IDE plugin (есть Snyk, Semgrep)
- **Не** CVE база (есть Snyk, Dependabot)
- **Не** deterministic SAST (есть Semgrep, Bandit)
- **Не** PR review bot (есть CodeRabbit, Graphite)

**Vishap - комплементарен.** Не заменяет — дополняет.

---

## Как голосовать за features

GitHub Issues — https://github.com/dvddv9/vishap/issues

Метки:
- `roadmap/v5.8` — Q1 2027
- `roadmap/v6.0` — Q2-Q3 2027
- `roadmap/v6.1+` — 2028+

---

*Last updated: 2026-10-12 | Vishap V5.8*