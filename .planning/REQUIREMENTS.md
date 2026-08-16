# Requirements: RustyAlarm

**Defined:** 2026-08-15
**Core Value:** A subscribed player reliably receives a Discord alert within seconds of their Smart Alarm firing, 24/7, without keeping their own PC on.

> Brownfield note: the MVP for both products already exists. The **v1 Requirements** below are the
> *next milestone* (Production Subscription Launch) — the deferred backlog, not the built MVP.
> Already-shipped capabilities are recorded under **Validated (shipped in MVP)** for anchoring and
> are not mapped to next-milestone phases. Security IDs (`SEC-0NN`) are reused verbatim from
> `.planning/security-audit/2026-08-15/` to preserve traceability.

## v1 Requirements

Next-milestone scope. Each maps to exactly one roadmap phase.

### Quality & Stabilization

- [ ] **TEST-01**: Automated test suite (`tests/` with pytest + pytest-asyncio) covering SSRF reject, CSRF reject, security-header presence, session-hash round-trip, rate-limit thresholds, and alarm trigger + cooldown; runnable in CI.
- [ ] **STAB-01**: Fix the critical missing `import os` in `core.py` so `save_config()` (the SEC-009 per-pid temp write) no longer raises `NameError`; add a regression test.
- [ ] **SEC-014**: CI security scanning on every change (`pip-audit` + secret scan); optionally hash-pin `requirements.txt`; sign released PyInstaller desktop binaries.

### Backend Security Hardening

- [ ] **SEC-003**: App-layer per-endpoint rate limiter on session mint (`/auth/steam/return`), `/api/webhook/test`, and alarm create — independent of nginx `limit_req`.
- [ ] **SEC-006**: Stop streaming `player_token` / `discord_webhook` in the ~2s poll payload; send `has_webhook` and fetch secrets on-demand only when editing, without breaking wizard edit prefill.
- [ ] **SEC-010**: Rotate the session token on re-login (invalidating the old one) and expire idle sessions per policy, replacing the fixed 30-day no-rotation expiry.

### Frontend Polish & CSP Hardening

- [ ] **FE-01**: On-screen visual/QA review of landing, panel, and admin pages with fresh eyes; fine details tuned; no visual regressions (the redesign was previously validated only by DOM/measurement).
- [ ] **FE-02**: Run `find-animation-opportunities` over `saas/templates/` and the landing to produce a concrete, prioritized list of animation improvements.
- [ ] **SEC-011**: Remove `'unsafe-inline'` from the CSP `script-src` by moving inline JS to external files with per-response nonces; pages still function.

### Payments & Subscription

- [ ] **PAY-01**: Integrate a payment provider that drives `plan_active` — a successful payment activates/renews the plan; a lapsed payment deactivates it and the `Manager` stops that user's alarm runners; replaces manual toggling.

### Production Deployment & Operations

- [ ] **DEPLOY-01**: Execute `deploy/DEPLOY.md` on the real Ubuntu VPS — service under `deploy/rustyalarm.service` behind nginx with valid TLS, and the Steam login callback works against the live `RUSTALARM_BASE_URL`.
- [ ] **OPS-01**: Operational scripts — a cron-scheduled `deploy/backup.sh` backing up `saas_data/`, and a documented one-line update path.

## Validated (shipped in MVP)

Already built and confirmed working per the 2026-08-15 session logs; not part of the next milestone.

- ✓ **WIZ-01**: 7-step guided alarm-creation wizard (Welcome → Name → Server → Alarm → Discord → Settings → Summary) with per-step validation, first-alarm onboarding, collapsible in-app guides, end summary, and edit mode.
- ✓ **WHT-01**: `POST /api/webhook/test` sends a test Discord embed so users can validate a webhook before saving (invalid → 400, valid → embed delivered).

## v2 Requirements

Acknowledged, deferred beyond this milestone.

### Reliability

- **RETRY-01**: Persistent retry / dead-letter queue for failed Discord webhook deliveries. *(Touches Core Value — a dropped webhook is a missed raid. Candidate to pull forward if reliability slips.)*
- **LOG-01**: Thread/async-safe locking around monitor log deques to prevent lost/duplicated entries under concurrency.

### Scale & Ops

- **SCALE-01**: Horizontal scaling of the SaaS monitor via message queue or leader election (removes the single-worker constraint).
- **DB-01**: Migrate SQLite → PostgreSQL when the user base exceeds ~50-100.
- **OBS-01**: Structured logging + metrics/alerting for alarm success/failure rates and system health.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-worker SaaS deployment today | In-memory `manager` state → duplicate alerts; needs SCALE-01 refactor first |
| Desktop cross-platform support | `winsound` is Windows-only by design; no fallback planned |
| Non-Discord alert channels (SMS, email, push) | Discord is the sole intended sink for this milestone |
| Alternative auth (email/password, other OAuth) | Steam OpenID ties identity to the game account and is sufficient |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TEST-01 | Phase 1 | Pending |
| STAB-01 | Phase 1 | Pending |
| SEC-014 | Phase 1 | Pending |
| SEC-003 | Phase 2 | Pending |
| SEC-006 | Phase 2 | Pending |
| SEC-010 | Phase 2 | Pending |
| FE-01 | Phase 3 | Pending |
| FE-02 | Phase 3 | Pending |
| SEC-011 | Phase 3 | Pending |
| PAY-01 | Phase 4 | Pending |
| DEPLOY-01 | Phase 5 | Pending |
| OPS-01 | Phase 5 | Pending |

**Coverage:**
- v1 (next-milestone) requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-15*
*Last updated: 2026-08-15 after new-project bootstrap from ingest*
