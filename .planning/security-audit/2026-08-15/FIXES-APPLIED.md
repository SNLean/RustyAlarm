# Fixes applied — 2026-08-15

`/revisar` is audit-only; these fixes were applied as an explicit follow-up (user asked to "fixealas"). Each was verified.

| Finding | Fix | Status |
|---|---|---|
| SEC-001 | Desktop `webapp.py`: `_csrf_ok()` requires `application/json` + validates `Origin`; blocks cross-site simple-request CSRF | **fixed** (live: text/plain→403, cross-origin→403, same-origin JSON→200) |
| SEC-002 | `saas/db.py`: `is_blocked_host()` rejects private/loopback/link-local/metadata; wired into `validate_alarm` | **fixed** (live: 127.0.0.1 rejected, public OK) |
| SEC-003 | nginx `limit_req` on `/login`,`/auth/steam/return`,`/api/`; `name`/`server` length-capped in `/api/webhook/test` | **partial** (nginx throttle + field caps; app-layer per-endpoint limiter deferred) |
| SEC-004 | `admin.html`: added `esc()` and wrapped all interpolations | **fixed** |
| SEC-005 | `saas/db.py`: session tokens stored as `sha256` (`_hash_token`); cookie keeps raw token | **fixed** (live: hashed at rest, lookup works). Note: invalidates pre-existing sessions once. |
| SEC-006 | Discord failure no longer echoes the exception (which could carry the webhook URL) in `app.py` and `monitor.py` | **partial** (error/log redaction done; poll-payload minimization deferred — UX) |
| SEC-007 | Desktop `_send()` adds `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, CSP | **fixed** (live: headers present) |
| SEC-008 | `deploy/nginx.conf`: `server_tokens off;` + HSTS note for the 443 block | **fixed** |
| SEC-009 | `core.py` `save_config`: unique per-pid temp filename | **fixed** |
| SEC-012 | `saas/steam.py`: exact-line `is_valid:true` match instead of substring | **fixed** |
| SEC-013 | `saas/app.py`: startup warning when `BASE_URL` is non-https and non-local | **fixed** |

## Deferred (need a decision or larger work)

- **SEC-003 app-layer limiter** — nginx handles it in production; an in-process limiter needs a design choice (per-session vs per-IP store).
- **SEC-006 poll minimization** — not sending `player_token`/`discord_webhook` in the 2s poll breaks the wizard's edit prefill; needs a UX change (send `has_webhook` + fetch secrets on edit).
- **SEC-010** session rotation/idle policy — optional.
- **SEC-011** CSP `unsafe-inline` removal — requires moving inline JS to files + nonces (template refactor).
- **SEC-014** CI security scanning + signed binaries — process/infra, not code.
