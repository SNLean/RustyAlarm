# Context

Topic-keyed running notes distilled from the six 2026-08-15 session logs (all DOC type)
and the grounding codebase/security-audit maps. Each note carries source attribution.

## Project overview
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — README and official docs.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md
- RustyAlarm is a Rust (game) raid-alarm notification system with two products sharing only the `rustplus` library: a multi-user FastAPI SaaS subscription service and a single-user Windows desktop tool. The repo `README.md` is the official front door; internal docs live in the Obsidian vault under `docs/` (thematic notes + `References/` + `Log/`).

## Evolution: from script to service
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md
- In one session RustyAlarm went from a loose script to a hosted service: initial `CLAUDE.md` agent guide; desktop refactor; panel pairing guides aligned to official docs; a full subscription service under `saas/`; adversarial review; private git repo; Ubuntu VPS + nginx deploy assets; and the Obsidian vault. Sources consulted: rustplus (olijeffers0n) + docs, liamcottle/rustplus.js, FastAPI, Uvicorn deployment, Certbot.

## Desktop tool
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md
- Desktop = `core.py` (no import side effects) + `webapp.py` (local panel on `127.0.0.1:8765`) + `rust.py` (console), all over one `AlarmMonitor` (threaded asyncio loop, RLock-guarded state, single alarm). Config in `config.json` (atomic temp-file save). Old bugs fixed: stale `last_state` (sounded every poll), unapplied `COOLDOWN`, CWD-relative paths.

## SaaS subscription service
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md
- FastAPI/uvicorn (single worker) with Steam OpenID login, per-user alarms in SQLite, an asyncio Manager orchestrating one AlarmRunner coroutine per active alarm, Discord webhook alerts, and an env-gated `/admin` page. `Manager.sync()` reconciles DB alarms against live tasks (start/stop/restart on change, plan-inactive stop).

## Authentication (Steam OpenID)
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md, C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md
- Steam OpenID 2.0 flow in `saas/steam.py`; `state` generated with `secrets.token_urlsafe(24)`, constant-time compared on return; claimed ID must match `^https?://steamcommunity\.com/openid/id/(\d{17})$`; response validated by exact `is_valid:true` line match (SEC-012, was a loose substring). A real Steam login (`76561198383652437`) remained in the DB during wizard testing — a legitimate account, not deleted.

## Notifications (Discord)
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Guided alarm wizard.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md
- Alerts via `saas/notify.py::send_discord()` (httpx, 10s timeout, raises on non-2xx, structured embed). Webhook host-locked (SSRF-resistant). Users can validate a webhook before saving via `POST /api/webhook/test`.

## Deployment (VPS / nginx)
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md, C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — README and official docs.md
- Deploy assets for Ubuntu VPS + nginx: `deploy/rustyalarm.service`, `deploy/nginx.conf`, `deploy/DEPLOY.md`. Pending: run DEPLOY.md on the real VPS; integrate a payment provider (drives `plan_active`); optional `deploy/backup.sh` via cron + one-line update script.

## Security posture
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/SECURITY-REVIEW.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/FIXES-APPLIED.md
- Current `/revisar` audit: attack-surface map → 5 domain reviewers → per-finding adversarial verify (40 agents) + `pip-audit` (clean). 34 raw findings deduped/re-scored to 14: 0 critical, 0 high, 3 medium, 8 low, 3 info. Fixed & verified: SEC-001 (desktop CSRF), SEC-002 (SSRF blocklist), SEC-004 (admin.html escaping), SEC-005 (hashed session tokens), SEC-006 (error redaction), SEC-007 (desktop security headers), SEC-008 (nginx server_tokens off + limit_req + HSTS note), SEC-003 (field caps + nginx throttle), SEC-009 (per-pid temp save), SEC-012 (exact Steam is_valid match), SEC-013 (non-https BASE_URL startup warning). Prior review's fixes (tenant isolation, CSRF, panel XSS escaping, login state, parameterized SQL) re-verified as holding. Deferred: SEC-003 app-layer limiter, SEC-006 poll minimization, SEC-010 session rotation, SEC-011 CSP unsafe-inline removal, SEC-014 CI scanning + signed binaries. GSD was not initialized (no ROADMAP.md); plan advised `/gsd-onboard` first.

## Frontend / design system
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Frontend redesign.md
- Full redesign of the SaaS front using `frontend-design` (Anthropic), `emil-design-eng`, `animate`. Direction: elevate dark + Rust orange to premium around a live-signal monitoring motif. Token system in `base.html` (Rust vermilion `#db4325` + signal green, old names kept as aliases). Monospace telemetry; two-column hero with a monitoring console; elevated panel cards with rust glow on `.fired`; refined admin table. Motion: `:active{scale(.97)}` 130ms, IntersectionObserver reveal with 60ms stagger, toast slide+fade, ambient signal pulse, breathing alarm dot; `prefers-reduced-motion` respected. Verified by DOM/measurement (bg `#121010`, `--rust #db4325`, `ui-monospace`, card radius 14px); pending on-screen visual review (browser pane not compositing frames). `agents-design-experience@buildwithclaude` plugin not installed (not needed).

## Guided wizard UX
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Guided alarm wizard.md
- 7-step wizard in `saas/templates/panel.html` (Welcome → Name → Server → Alarm → Discord → Settings → Summary) with progress bar, per-step validation, Back/Next, first-alarm onboarding, collapsible in-app guides (pairing, entity ID, webhook), a summary flagging "no webhook — no alert", and edit mode (no welcome, pre-filled). Alignment fixes in `.wiz-body`: `scrollbar-gutter: stable` + `height: clamp(300px,54vh,460px)` for constant geometry; IP/Port row aligned via flex-column fields with `input{margin-top:auto}` + a help line on IP.

## Tooling / skills
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Design and animation skills.md
- Installed Emil Kowalski's 10 skills globally (`npx skills@latest add emilkowalski/skills -g -s '*' -y --copy`; 8 already present, new: `pick-ui-library`, `prototype`) and copied them into repo `skills/` (versioned). `pick-ui-library`/`prototype` are `disable-model-invocation: true`. Front is vanilla HTML/CSS/JS, so animation/design skills fit best; React ones (`ask-sonner`, `pick-ui-library`) less. Installer "Failed to install 10 → PromptScript" message is a different agent, harmless. Pending: run `find-animation-opportunities` over `saas/templates/` and the landing.

## Documentation & vault
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — README and official docs.md
- `README.md` written (was a 2-line stub) as the repo front door: what RustyAlarm is, getting started (`python -m saas`, `python webapp.py`), Rust+ data guide, docs index (vault, `deploy/DEPLOY.md`, `CLAUDE.md`), stack + security note. Vault is complete internal documentation, migrated to English (folders `Referencias/`→`References/`, `Registro/`→`Log/`); end-user-facing text stays Spanish.

## Session notes / quirks
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md, C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — From script to service.md
- The 34/34 "CONFIRMED" verifier rate was lenient (many low/info/dupes); Phase-5 dedup + manual re-scoring produced the realistic 14. `/revisar`'s workflow post-processing had a shape bug returning empty arrays — the journal was treated as the authoritative source. A git credential mismatch (git `BriYlean` vs repo `SNLean`) was resolved during setup.
