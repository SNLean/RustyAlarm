# Roadmap: RustyAlarm

## Overview

The MVP for both products is built and hardened (0 critical / 0 high in the 2026-08-15 security
audit). This roadmap is the **next milestone — Production Subscription Launch** — which takes the
already-working SaaS from a manually-toggled, un-deployed, untested MVP to a paid, hardened, live
24/7 service. The journey: stand up a test/CI safety net (and fix one critical defect the audit
missed) → close the deferred backend security items → review and harden the frontend → wire real
payments to `plan_active` → deploy to the VPS and add backup/update ops. Production deploy is the
capstone so the launch goes live with everything assembled. Granularity: **standard** (no
`config.json`; defaults applied — sequential phase IDs, no project code).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>✅ MVP (brownfield, un-tracked) — both products built + security-audited (2026-08-15)</summary>

The desktop tool and SaaS were built and hardened before GSD was initialized, so they are not
tracked as GSD phases. See PROJECT.md → Requirements → Validated for the shipped capabilities
(two-product architecture, Steam OpenID, per-user alarms, Discord alerts, guided wizard, webhook
test, premium frontend, deploy assets, security audit). Phases 1-5 below are the next milestone.

</details>

- [ ] **Phase 1: Quality Foundation — Tests, CI & Critical Fix** - Stand up the automated test suite, wire CI security scanning, and fix the crash-on-config-save defect.
- [ ] **Phase 2: Backend Security Hardening** - Close the deferred audit items: app-layer rate limiting, poll-payload secret minimization, session rotation.
- [ ] **Phase 3: Frontend Polish & CSP Hardening** - On-screen visual review, animation audit, and removal of CSP `unsafe-inline`.
- [ ] **Phase 4: Payments & Subscription Lifecycle** - Wire a payment provider to `plan_active` so paying starts alerts and lapsing stops them.
- [ ] **Phase 5: Production Deployment & Operations** - Go live on the Ubuntu VPS behind nginx + TLS, with backup and update ops.

## Phase Details

### Phase 1: Quality Foundation — Tests, CI & Critical Fix
**Goal**: A safety net exists — every future change is guarded by automated tests and CI scans, and the one known crashing defect is gone.
**Depends on**: Nothing (first phase)
**Requirements**: TEST-01, STAB-01, SEC-014
**Success Criteria** (what must be TRUE):
  1. Running `pytest` executes a `tests/` suite covering SSRF reject, CSRF reject, security-header presence, session-hash round-trip, rate-limit thresholds, and alarm trigger + cooldown — and it passes.
  2. The same suite runs in CI on every push/PR, alongside `pip-audit` and a secret scan, and the pipeline fails on a new vulnerability or leaked secret.
  3. Calling the desktop config-save path no longer raises `NameError` (the `os` import is present), proven by a regression test.
  4. Released desktop binaries are signed (or a documented, decided path to signing exists).
**Plans**: TBD

### Phase 2: Backend Security Hardening
**Goal**: The deferred backend security findings are closed, so the service defends itself even without nginx and stops leaking secrets to the browser.
**Depends on**: Phase 1
**Requirements**: SEC-003, SEC-006, SEC-010
**Success Criteria** (what must be TRUE):
  1. Rapid repeated POSTs to `/api/webhook/test` (and to session mint / alarm create) return HTTP 429 from the app itself, even with nginx removed.
  2. The ~2s poll response carries no raw `player_token` or `discord_webhook` (only `has_webhook`), yet the wizard's edit prefill still works via an on-demand secret fetch.
  3. Re-logging in issues a new session token and invalidates the previous one, and idle sessions expire per the defined policy.
**Plans**: TBD

### Phase 3: Frontend Polish & CSP Hardening
**Goal**: The user-facing pages are reviewed on real screens, animation gaps are catalogued, and the CSP no longer needs `unsafe-inline`.
**Depends on**: Phase 1
**Requirements**: FE-01, FE-02, SEC-011
**Success Criteria** (what must be TRUE):
  1. Landing, panel, and admin pages have been reviewed on-screen with fresh eyes, fine details tuned, and show no visual regressions.
  2. A concrete, prioritized list of animation opportunities for the templates and landing has been produced.
  3. The CSP `script-src` no longer allows `'unsafe-inline'`; all pages function with nonce'd / external JS.
**Plans**: TBD
**UI hint**: yes

### Phase 4: Payments & Subscription Lifecycle
**Goal**: Money drives access — a successful payment turns alerts on, a lapsed one turns them off, with no manual admin toggling.
**Depends on**: Phase 1, Phase 3
**Requirements**: PAY-01
**Success Criteria** (what must be TRUE):
  1. A user can reach a pricing page, complete checkout through the payment provider, and see `plan_active` become true automatically.
  2. A successful renewal keeps the plan active; a lapsed/failed payment sets `plan_active` false and the `Manager` stops that user's alarm runners.
  3. The admin no longer needs to toggle `plan_active` by hand for normal subscriptions.
**Plans**: TBD
**UI hint**: yes

### Phase 5: Production Deployment & Operations
**Goal**: The service is live 24/7 on the VPS with TLS, and its data survives failures — delivering the core promise without the player's PC.
**Depends on**: Phase 1, Phase 2, Phase 3, Phase 4
**Requirements**: DEPLOY-01, OPS-01
**Success Criteria** (what must be TRUE):
  1. The SaaS runs under `deploy/rustyalarm.service` behind nginx with valid TLS, and a real Steam login completes against the live `RUSTALARM_BASE_URL`.
  2. A subscribed user's Smart Alarm firing produces a Discord alert within ~5s from the live service, with the user's PC off.
  3. `saas_data/` is backed up on a cron schedule and a single-command update path is documented and works.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Quality Foundation — Tests, CI & Critical Fix | 0/TBD | Not started | - |
| 2. Backend Security Hardening | 0/TBD | Not started | - |
| 3. Frontend Polish & CSP Hardening | 0/TBD | Not started | - |
| 4. Payments & Subscription Lifecycle | 0/TBD | Not started | - |
| 5. Production Deployment & Operations | 0/TBD | Not started | - |
