# RustyAlarm

## What This Is

RustyAlarm is a Rust (the game) raid-alarm notification system built as two isolated
products that share only the `rustplus` library: a multi-user **FastAPI SaaS** subscription
service (`saas/`) that watches players' Rust+ Smart Alarms and pushes Discord alerts, and a
single-user **Windows desktop tool** (`core.py` / `webapp.py` / `rust.py`) that plays a local
sound. The SaaS is the product being taken to a paid subscription; the desktop tool is a
localhost companion.

## Core Value

A subscribed player reliably receives a Discord alert within seconds of their Smart Alarm
firing, 24/7, without keeping their own PC on. If everything else fails, alert delivery must not.

## Business Context

- **Customer**: Rust players who run in-game Smart Alarms and want raid alerts even when their PC is off.
- **Revenue model**: Subscription gated by `users.plan_active` (today toggled manually; moving to a payment provider).
- **Success metric**: A subscribed user reliably receives a Discord alert within ~5s of their Smart Alarm firing, 24/7, without keeping their own PC on.

## Requirements

### Validated

<!-- Shipped in the MVP (brownfield) and confirmed working per the 2026-08-15 session logs + security audit. -->

- ✓ **Two-product architecture** — SaaS (`saas/`) + Windows desktop tool, sharing only `rustplus` — MVP
- ✓ **Steam OpenID 2.0 login** for the SaaS; random session tokens hashed at rest — MVP
- ✓ **Per-user alarm CRUD** in SQLite, isolated by Steam ID; async `Manager`/`AlarmRunner` polling — MVP
- ✓ **Discord webhook alerts** (host-locked, SSRF-resistant) as the SaaS notification sink — MVP
- ✓ **WIZ-01** Guided 7-step alarm-creation wizard with per-step validation and in-app guides — MVP
- ✓ **WHT-01** `POST /api/webhook/test` validates a Discord webhook before saving — MVP
- ✓ **Premium monitoring frontend** (dark + Rust-vermilion, monospace telemetry, disciplined motion) — MVP
- ✓ **Deploy assets authored** (`deploy/rustyalarm.service`, `nginx.conf`, `DEPLOY.md`) — MVP
- ✓ **Security audit passed** — 0 critical/0 high; 11 findings fixed and verified — MVP

### Active

<!-- Next milestone: take the hardened MVP to a paid, production, tested service. -->

- [ ] **TEST-01** Automated test suite (pytest + pytest-asyncio) with security/behavior regressions, runnable in CI
- [ ] **STAB-01** Fix critical `os`-import defect in `core.py` that crashes `save_config()`
- [ ] **SEC-014** CI security scanning (pip-audit + secret scan); optional hash-pinned requirements + signed binaries
- [ ] **SEC-003** App-layer per-endpoint rate limiter (defense-in-depth beyond nginx)
- [ ] **SEC-006** Poll-payload secret minimization (`has_webhook` + on-demand secret fetch)
- [ ] **SEC-010** Session rotation on re-login + idle-timeout policy
- [ ] **FE-01** On-screen visual/QA review of landing, panel, and admin pages
- [ ] **FE-02** Animation-opportunity audit over `saas/templates/` and the landing
- [ ] **SEC-011** Remove CSP `script-src 'unsafe-inline'` (inline JS → external files + nonces)
- [ ] **PAY-01** Payment-provider integration driving `plan_active` (activate/renew/deactivate)
- [ ] **DEPLOY-01** Execute `deploy/DEPLOY.md` on the real Ubuntu VPS (systemd + nginx + TLS)
- [ ] **OPS-01** Operational scripts — cron backup of `saas_data/` + one-line update path

### Out of Scope

- **Horizontal scaling / multi-worker SaaS** — in-memory `manager` state mandates a single uvicorn worker; needs a message-queue or leader-election refactor. Deferred to v2.
- **PostgreSQL migration** — SQLite (WAL + RLock) is sufficient for tens of users; revisit past ~50-100 users.
- **Discord delivery retry queue** — a dropped webhook = a missed raid, which touches Core Value; flagged as v2 and a candidate to pull forward if reliability slips.
- **Structured logging / metrics / observability stack** — nice-to-have ops maturity, not launch-critical.
- **Desktop cross-platform support** — `winsound` is Windows-only by design; no fallback planned.

## Context

Brownfield project. The MVP for both products is built and hardened; a full security audit
(`/revisar`) ran on 2026-08-15 producing 14 deduped findings (0 critical, 0 high, 3 medium,
8 low, 3 info), of which 11 were fixed and verified. GSD was not previously initialized — this
is the first tracked milestone, and it starts from the deferred backlog rather than re-planning
the already-built MVP. The frontend redesign was validated only by DOM/measurement (the browser
pane was not compositing frames), so an on-screen review is still owed. One critical code defect
survived the audit: `core.py` uses `os.getpid()` without importing `os`, crashing config save on
the desktop tool. Sources: `.planning/intel/*`, `.planning/codebase/*`,
`.planning/security-audit/2026-08-15/*`.

## Constraints

- **Tech stack**: Python 3.14. SaaS = FastAPI + Uvicorn (single worker) + SQLite; desktop = stdlib `http.server` + `winsound` (Windows-only); shared dep `rustplus==6.0.9`.
- **Single worker (SaaS)**: Alarm state lives in the in-memory `manager` — multiple workers spawn every alarm in each worker → duplicate Discord alerts. Horizontal scaling needs a queue/leader-election refactor.
- **rustplus 6.x semantics**: Library never raises; it signals failure via return values (`False`, `RustError`). Code must check return values, not rely on try/except.
- **SQLite WAL + global RLock**: All DB access serialized by a module-level RLock; monitor coroutines call DB via `asyncio.to_thread()`. Filesystem must support `*-wal`/`*-shm`.
- **Steam login**: `RUSTALARM_BASE_URL` must exactly match the public domain or the OpenID callback fails; HTTPS terminates at nginx; FastAPI trusts `X-Forwarded-*` only from `forwarded_allow_ips`.
- **Big integers as strings**: Steam IDs / player tokens / entity IDs exceed JS `MAX_SAFE_INTEGER` → travel as strings, validated to int on the server; alarm numeric fields fit signed int32.
- **Security invariants**: validation-first before any storage; tenant isolation by `steam_id` on every query; CSRF same-origin on mutating routes; SSRF blocklist on the user-supplied alarm host; secrets env-only (`RUSTALARM_` prefix), never in source or logs.
- **Frontend**: no external fonts (CSP `font-src 'self'`, system monospace); motion durations <300ms; `prefers-reduced-motion` honored.

## Key Decisions

<!-- All decisions below are DOC-derived (session logs) and PROPOSED — none are ADR-locked.
     Most are already implemented in the MVP; they can still be revisited. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two isolated products sharing only `rustplus` | SaaS and desktop have different concurrency models (async Manager vs threaded monitor) | ✓ Implemented (proposed) |
| Steam OpenID 2.0 for SaaS auth; unsigned random tokens hashed at rest | No password storage; ties identity to the game account | ✓ Implemented (proposed) |
| Discord webhooks as sole alert sink (host-locked) | Ubiquitous with Rust communities; SSRF-containable | ✓ Implemented (proposed) |
| SQLite (WAL + RLock) as the datastore | Sufficient for tens of users; zero-ops | ✓ Implemented (proposed) |
| Single uvicorn worker | In-memory monitor state; avoids duplicate alerts | ✓ Implemented (proposed) |
| VPS on Ubuntu + nginx (TLS via Certbot) | Simple, cheap, full control for a 24/7 poller | ✓ Assets authored, not yet deployed (proposed) |
| Guided 7-step wizard over one dense form | New users couldn't tell where the four pairing values come from | ✓ Implemented (proposed) |
| Premium "live-signal" monitoring frontend identity | Sell trust in an always-watching service | ✓ Implemented; on-screen review owed (proposed) |
| Vault/internal docs English; end-user UI stays Spanish | Better tooling/recall internally; native UX for users | ✓ Implemented (proposed) |
| No payment provider yet — manual `plan_active` | Ship monitoring first, monetize second | ⚠️ Revisit — replaced this milestone by PAY-01 |

---
*Last updated: 2026-08-15 after new-project bootstrap from ingest (brownfield MVP).*
