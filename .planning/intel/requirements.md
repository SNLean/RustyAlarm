# Requirements

> Provenance note: Extracted from DOC-precedence session logs and the grounding
> codebase/security-audit maps. Requirements marked "(implemented)" already exist in
> code per the session logs; the rest are forward-looking / backlog. No PRD sources
> exist, so there are no competing acceptance variants.

## REQ-payments-integration
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/STACK.md
- description: Integrate a payment provider that drives `plan_active`, replacing manual plan activation.
- acceptance: Successful payment automatically sets/renews `plan_active` for the paying user; lapsed payment deactivates the plan (and the Manager stops that user's alarm runners). Backlog — not yet started.
- scope: billing, subscription lifecycle

## REQ-vps-production-deploy
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md
- description: Execute the `deploy/DEPLOY.md` steps on the real Ubuntu VPS (systemd unit + nginx + TLS).
- acceptance: Service runs under `deploy/rustyalarm.service` behind nginx with valid TLS; Steam login callback works against the live `RUSTALARM_BASE_URL`. Pending.
- scope: deployment, operations

## REQ-deploy-ops-scripts
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md
- description: Optional operational scripts — `deploy/backup.sh` run via cron and a one-line update script.
- acceptance: Scheduled backups of `saas_data/` produced by cron; single-command update path documented and working. Optional / backlog.
- scope: operations, backup

## REQ-automated-test-suite
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/TESTING.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/GSD-REMEDIATION.md
- description: Introduce an automated test suite (none exists today). Priority: validation logic, security checks (SSRF/CSRF), alarm trigger + cooldown, DB concurrency.
- acceptance: `tests/` with pytest + pytest-asyncio; regression tests for SSRF reject, CSRF reject, security-header presence, session-hash round-trip, and rate-limit thresholds; runnable in CI. Backlog.
- scope: testing, quality

## REQ-design-visual-review
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Frontend redesign.md
- description: Perform the pending visual/screenshot review of the redesigned landing/panel/admin. This session validated only by DOM/measurement because the browser pane was not compositing frames.
- acceptance: All three pages reviewed on-screen with fresh eyes; fine details tuned; no visual regressions. Pending.
- scope: frontend, QA

## REQ-animation-audit
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Design and animation skills.md
- description: Run `find-animation-opportunities` over `saas/templates/` and the landing to identify concrete animation improvement points.
- acceptance: A list of concrete, prioritized animation opportunities produced for the vanilla panel/landing. Pending.
- scope: frontend, animation

## REQ-guided-alarm-wizard (implemented)
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Guided alarm wizard.md
- description: 7-step guided alarm-creation wizard in `saas/templates/panel.html` with progress bar, per-step validation, Back/Next, first-alarm onboarding, in-app collapsible guides, end summary, and edit mode (reuses wizard, no welcome, pre-filled).
- acceptance: Panel renders 7 steps + 3 guides + test button; empty name blocks step; full create via final-submit → 200; edit pre-fills without welcome; no console errors. Verified implemented.
- scope: UX, alarm creation

## REQ-webhook-test-endpoint (implemented)
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Guided alarm wizard.md
- description: `POST /api/webhook/test` (`saas/app.py`) with `db.is_discord_webhook()` sends a test embed so users can validate a Discord webhook before saving.
- acceptance: Invalid/empty webhook → 400; valid webhook → test embed delivered. Verified implemented (name/server length-capped per SEC-003).
- scope: notifications, validation

## REQ-sec-app-rate-limiter (SEC-003 deferred)
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/FIXES-APPLIED.md
- description: Add an app-layer per-endpoint rate limiter on session mint (`/auth/steam/return`), the Discord-relay wizard endpoint (`/api/webhook/test`), and alarm create. nginx `limit_req` + field caps already applied; in-process limiter deferred pending a per-session-vs-per-IP design choice.
- acceptance: Rapid `/api/webhook/test` returns 429 at the app layer independent of nginx. Deferred / backlog.
- scope: security, abuse prevention

## REQ-sec-poll-payload-minimization (SEC-006 deferred)
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/FIXES-APPLIED.md
- description: Stop streaming `player_token`/`discord_webhook` in the ~2s poll payload; send `has_webhook` and fetch secrets only on edit. Error/log redaction of the webhook URL is already done; payload minimization deferred because it breaks the wizard's edit prefill (needs a UX change).
- acceptance: Poll responses carry no raw secrets; wizard edit prefill still works via on-demand secret fetch. Deferred / backlog.
- scope: security, secret handling, UX

## REQ-sec-session-rotation (SEC-010 deferred)
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/SECURITY-REVIEW.md
- description: Add session rotation on re-login and an idle policy (currently a fixed 30-day expiry with no rotation).
- acceptance: Re-login issues a new token and invalidates the old; idle sessions expire per policy. Deferred / optional.
- scope: security, sessions

## REQ-sec-csp-no-unsafe-inline (SEC-011 deferred)
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/GSD-REMEDIATION.md
- description: Remove `'unsafe-inline'` from the CSP `script-src` by moving inline JS to files + nonces. Larger template refactor; schedule separately.
- acceptance: CSP no longer allows `'unsafe-inline'` for scripts; pages function with nonce'd/external JS. Deferred (high change risk).
- scope: security, CSP, frontend refactor

## REQ-sec-ci-scanning-signed-binaries (SEC-014 deferred)
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/SECURITY-REVIEW.md
- description: Add CI security scanning (`pip-audit` + secret scan), consider hash-pinned `requirements`, and sign the PyInstaller binaries.
- acceptance: CI runs the scans on each change; requirements optionally hash-pinned; released binaries signed. Deferred (process/infra).
- scope: security, supply chain, CI
