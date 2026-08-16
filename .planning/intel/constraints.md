# Constraints

> Provenance note: Extracted from DOC-precedence session logs plus the grounding
> codebase/security-audit maps. These are standing technical/operational invariants the
> roadmapper must respect.

## Single uvicorn worker only (SaaS)
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/STACK.md
- type: nfr
- content: Alarm state lives in the in-memory `manager` (single process). Multiple uvicorn/gunicorn workers each spawn every alarm → duplicate Discord alerts and Rust+ calls. Mandated in `saas/__main__.py`. Horizontal scaling requires a message queue or leader-election refactor.

## SQLite WAL + global RLock
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/STACK.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md
- type: schema
- content: `saas_data/rustalarm.db` runs in WAL mode; all access is serialized by a module-level RLock in `saas/db.py`. Filesystem must support `*-wal`/`*-shm`. Monitor coroutines call DB via `asyncio.to_thread()` to avoid blocking the event loop while the lock is held. `PRAGMA foreign_keys=ON`; indexes on `alarms(steam_id)` and `sessions(expires_at)`.

## rustplus pinned to 6.x
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/STACK.md
- type: protocol
- content: `rustplus==6.0.9`, strictly 6.x — older/newer versions have a different `RustSocket` shape. The library never raises exceptions; it signals failure via return values (`False`, `RustError`). Code must check return values, not rely on try/except.

## Desktop tool is Windows-only
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/STACK.md
- type: nfr
- content: The desktop tool depends on `winsound` (no fallback), so it runs on Windows only. Shipped as a PyInstaller `.exe`. The SaaS runs on any Python 3.14 platform.

## Big integers travel as strings
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/STACK.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md
- type: schema
- content: Steam IDs / player tokens / entity IDs exceed JS `MAX_SAFE_INTEGER`, so they travel as strings over the wire and are validated back to integers on the server. Alarm numeric fields must fit signed 32-bit range.

## Steam login requires exact BASE_URL match, behind a reverse proxy
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/STACK.md
- type: protocol
- content: `RUSTALARM_BASE_URL` must exactly match the public domain or the Steam OpenID callback fails. HTTPS terminates at nginx; FastAPI trusts `X-Forwarded-*` only from `forwarded_allow_ips` (`RUSTALARM_FORWARDED_IPS`, default `127.0.0.1`). SaaS binds `127.0.0.1:8000` by default.

## Frontend: no external fonts, disciplined motion
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Frontend redesign.md
- type: nfr
- content: CSP `font-src` falls back to `'self'`, so no external font loading — telemetry uses system monospace (`ui-monospace`). Motion tokens use a strong `--ease-out` with durations <300ms; `prefers-reduced-motion` globally neutralizes transforms/animations; hovers gated by `@media (hover:hover)`.

## Tenant / session isolation on every DB access
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/SECURITY-REVIEW.md
- type: api-contract
- content: Every SaaS DB read/write is scoped by `user["steam_id"]`; no user can access another's alarms. Verified holding in the security review (tenant isolation).

## CSRF defenses on mutating routes
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/FIXES-APPLIED.md
- type: api-contract
- content: SaaS mutating routes require `same_origin()` (Origin/Referer scheme+netloc match). Desktop `webapp.py` requires `application/json` content-type and validates `Origin` (`_csrf_ok()`), blocking cross-site simple-request writes. OAuth `state` cookie checked on return.

## SSRF blocklist on user-supplied alarm host
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md, C:/Users/PC/Desktop/RUST APP/.planning/security-audit/2026-08-15/FIXES-APPLIED.md
- type: api-contract
- content: `db.is_blocked_host()` rejects private/loopback/link-local/reserved/multicast/metadata addresses and `.local`/`.internal` suffixes; wired into `validate_alarm`. The Rust+ socket is the only egress sink dialing a user-supplied host:port; Steam and Discord sinks are host-locked.

## Session tokens: random, hashed at rest, not signed
- source: C:/Users/PC/Desktop/RUST APP/docs/Log/2026-08-15 — Security audit and fixes.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/STACK.md
- type: schema
- content: Session tokens are random (unsigned); stored as sha256 in `sessions` (`_hash_token`), cookie keeps the raw token; fixed 30-day expiry, no rotation yet (see REQ-sec-session-rotation). Hashing change invalidates pre-existing sessions once on deploy.

## Validation-first before any storage
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/ARCHITECTURE.md, C:/Users/PC/Desktop/RUST APP/.planning/codebase/TESTING.md
- type: api-contract
- content: All input is validated and normalized before DB/file write — `validate_alarm()` (SaaS, `saas/db.py`) and `validate_config()` (desktop, `core.py`) return clean typed dicts or raise `ValidationError`/`ConfigError` with per-field messages → handler returns 400. Never insert the raw payload.

## Secrets only via env vars; nothing in source
- source: C:/Users/PC/Desktop/RUST APP/.planning/codebase/STACK.md
- type: nfr
- content: SaaS config comes from `RUSTALARM_`-prefixed env vars (`BASE_URL`, `HOST`/`PORT`, `ADMIN_STEAM_ID`, `MAX_ALARMS` default 3, `DATA_DIR`, `FORWARDED_IPS`). `.env` is gitignored (`.env.example` provided). No secrets in source. Errors/logs must never echo the Discord webhook URL.
