# Security Review — RustyAlarm

**Date:** 2026-08-15 · **Branch/commit:** main @ b327897 · **Command:** `/revisar analiza todo mi codigo … y fixealas`

## Executive summary

- **Scope:** all application code — `saas/` (multi-tenant service), the desktop tool (`core.py`/`webapp.py`/`rust.py`/`web/`), `deploy/`, dependencies. Excluded: vendored `skills/`, audit tooling `.claude/`, the `docs/` vault, generated dirs.
- **Method:** attack-surface map → 5 parallel domain reviewers → per-finding adversarial verification (40 agents) + `pip-audit`. 34 raw findings deduped to 14.
- **Counts (post-dedupe, re-scored):** critical 0 · high 0 · **medium 3** · low 8 · info 3.
- **No CRITICAL/HIGH.** Much of `saas/` was hardened in a prior review; those fixes were re-verified as holding (tenant isolation, CSRF on mutating routes, panel XSS escaping, login `state`, parameterized SQL, admin gating env-only).

### Top risks
1. **SEC-001 (medium)** — Desktop panel localhost endpoints have no CSRF/Origin defense; a malicious web page can overwrite `config.json` or redirect the monitor via a cross-site simple request.
2. **SEC-002 (medium)** — SSRF: alarm IP/host is not blocklisted, so the server will dial arbitrary internal/loopback/metadata addresses.
3. **SEC-003 (medium)** — No rate limiting on session mint, the Discord-relay wizard endpoint, or alarm create; authenticated Discord-relay spam + amplification.

No CRITICAL/HIGH finding remains `NOT_VERIFIED`. One low item (`SEC-014`, dependency hash/CVE completeness) is partly `NOT_VERIFIED` beyond `pip-audit` (clean).

## Attack surface (from the mapper)

- **SaaS HTTP** (`saas/app.py`, FastAPI, single worker behind nginx): auth-gated alarm CRUD + admin, all mutating routes carry `same_origin()`; alarm queries scoped by `steam_id` (tenant isolation verified). Anon→auth mint at `/auth/steam/return`.
- **Desktop HTTP** (`webapp.py`, `127.0.0.1:8765`): sole gate is a Host-header allowlist — no session/CSRF (SEC-001/007).
- **Egress** (3 sinks): Steam (fixed host/TLS), Discord (host-locked, SSRF-resistant), **Rust+ socket to user-supplied host:port** (SEC-002).
- **Persistence:** SQLite WAL under a global lock; all SQL parameterized; MAX_ALARMS check atomic.

## Findings

Full machine-readable detail in `FINDINGS.json`. Summary:

| ID | Sev | Title | Component |
|---|---|---|---|
| SEC-001 | medium | Desktop localhost endpoints lack CSRF/Origin defense | webapp.py |
| SEC-002 | medium | SSRF: no private/loopback blocklist on alarm host | saas/db.py, monitor.py |
| SEC-003 | medium | No rate limiting; Discord-relay wizard + uncapped fields | saas/app.py, nginx.conf |
| SEC-004 | low | admin.html innerHTML without escaping (latent XSS) | admin.html |
| SEC-005 | low | Session tokens stored plaintext at rest | saas/db.py |
| SEC-006 | low | Secrets streamed each poll + webhook in error/log text | saas/app.py, notify.py |
| SEC-007 | low | Desktop panel missing X-Frame-Options/CSP/nosniff | webapp.py |
| SEC-008 | low | nginx version disclosure; no HSTS | deploy/nginx.conf |
| SEC-009 | low | Desktop config.json save races on shared temp file | webapp.py |
| SEC-010 | info | No session rotation on re-login; fixed 30-day expiry | saas/app.py, config.py |
| SEC-011 | info | CSP allows 'unsafe-inline' script-src (defense-in-depth) | saas/app.py |
| SEC-012 | info | Steam OpenID validity via loose substring match | saas/steam.py |
| SEC-013 | info | SECURE_COOKIES/CSRF derive from BASE_URL | saas/config.py, app.py |
| SEC-014 | info | No CI security scanning; unsigned binaries; no hash pin | repo |

## Tools

- `pip-audit -r requirements.txt` → **no known vulnerabilities** (fastapi 0.141.1, uvicorn 0.52.3, jinja2 3.1.6, httpx 0.28.1, python-multipart 0.0.32, rustplus 6.0.9).
- No CI/container/IaC scanners present (`TOOL_NOT_AVAILABLE`).

## Not verified

- Full transitive-CVE reachability beyond `pip-audit` (no lockfile with hashes).
- Runtime behavior behind a real nginx/TLS deployment (config reviewed statically).

No confirmed vulnerabilities were found beyond those listed; the above are the material areas reviewed.
