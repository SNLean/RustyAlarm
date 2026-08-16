# Decisions

> Provenance note: All entries below are derived from DOC-precedence session logs
> (lowest precedence in `ADR > SPEC > PRD > DOC`). No ADR/SPEC/PRD sources exist in
> this ingest set and none are `locked`. Every decision is therefore `status: proposed`
> — treat as authoritative-project-intent seeds for the roadmapper, not as locked ADRs.

## Two-product architecture: SaaS service + single-user desktop tool
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md
- status: proposed
- decision: RustyAlarm ships as two isolated products sharing only the `rustplus` library — a multi-user FastAPI SaaS (`saas/`) and a single-user desktop tool (`core.py`/`webapp.py`/`rust.py`). Each has its own monitor implementation (async Manager/AlarmRunner vs threaded AlarmMonitor).
- scope: overall architecture, product boundaries

## Steam OpenID 2.0 as SaaS authentication
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md
- status: proposed
- decision: SaaS user authentication is Steam OpenID 2.0 login; sessions are random tokens (not signed), hashed at rest. Desktop tool has no auth (localhost-only).
- scope: authentication, SaaS login

## Discord webhooks as the alert delivery channel
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md
- status: proposed
- decision: Raid-alarm alerts are delivered via user-supplied Discord webhooks (host-locked, SSRF-resistant). This is the sole notification sink for the SaaS.
- scope: notifications, alerting

## No payment provider yet — manual plan activation
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md
- status: proposed
- decision: No payments integration for now; plans are activated manually (`plan_active` set by hand). A payment provider is deferred (see REQ-payments-integration).
- scope: billing, subscription lifecycle

## VPS hosting on Ubuntu + nginx
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md
- status: proposed
- decision: The SaaS is deployed to an Ubuntu VPS behind nginx as reverse proxy, with systemd unit (`deploy/rustyalarm.service`), `deploy/nginx.conf`, and `deploy/DEPLOY.md`. HTTPS terminates at nginx (Certbot).
- scope: hosting, deployment topology

## SQLite as the SaaS datastore
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/STACK.md
- status: proposed
- decision: SaaS persistence is SQLite (`saas_data/rustalarm.db`) in WAL mode under a global RLock; tables `users`, `sessions`, `alarms`. Per-user alarms scoped by Steam ID.
- scope: persistence, datastore

## Desktop refactor into core.py / webapp.py / rust.py over one AlarmMonitor
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md
- status: proposed
- decision: The desktop code is split into `core.py` (no import side effects), `webapp.py` (local panel), and `rust.py` (console), all driving a single `AlarmMonitor`. Legacy bugs fixed (stale `last_state`, unapplied `COOLDOWN`, CWD-relative paths).
- scope: desktop tool architecture

## Private GitHub repo with gitignored secrets
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md
- status: proposed
- decision: Code lives in private repo `SNLean/RustyAlarm` with `.gitignore` excluding secrets, plus `requirements.txt`, `.env.example`, `config.example.json`. (Credential mismatch git=`BriYlean` vs repo=`SNLean` resolved.)
- scope: source control, secrets hygiene

## Vault/internal docs in English; end-user UI stays Spanish
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — README and official docs.md
- status: proposed
- decision: The Obsidian docs vault and internal documentation are maintained in English (better tooling/recall); everything the end user sees stays in Spanish. Rule recorded in [[Maintaining this vault]]. Folders renamed `Referencias/`→`References/`, `Registro/`→`Log/`.
- scope: documentation, i18n policy

## Vendor design/animation skills into the repo
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Design and animation skills.md
- status: proposed
- decision: Emil Kowalski's 10 skills (plus Anthropic `frontend-design`) are copied into repo `skills/` (with `skills/README.md`) so they are versioned with the project, in addition to the global install. `pick-ui-library`/`prototype` carry `disable-model-invocation: true`.
- scope: tooling, developer workflow

## Frontend design direction: premium monitoring identity
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Frontend redesign.md
- status: proposed
- decision: Elevate the dark + Rust-orange identity to premium around a "live signal / we are watching 24-7" monitoring motif. Token system in `base.html` (refined Rust vermilion `#db4325` + signal green, radius/shadow/motion scales, old names kept as aliases). Monospace for all telemetry; no external fonts (CSP `font-src 'self'`); motion durations <300ms; `prefers-reduced-motion` honored.
- scope: frontend, design system, UX

## Guided step-by-step wizard replaces the dense single alarm form
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Guided alarm wizard.md
- status: proposed
- decision: Alarm creation moves from one dense form to a 7-step guided wizard (Welcome → Name → Server → Alarm → Discord → Settings → Summary) with onboarding, per-step validation, and in-app collapsible guides, because new users could not tell where the four pairing values came from.
- scope: UX, onboarding, alarm creation
