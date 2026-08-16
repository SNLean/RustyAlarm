---
title: 2026-08-15 — Security audit and fixes
tags:
  - log
  - session
  - security
date: 2026-08-15
---

# 2026-08-15 — Security audit and fixes

Ran the user-authored `/revisar` skill (installed this session) over the whole app, then applied the fixes. See [[Security review]] for the standing invariants.

## Audit

- Pipeline: attack-surface map → 5 parallel domain reviewers → per-finding adversarial verify (40 agents) + `pip-audit` (clean). Report under `.planning/security-audit/2026-08-15/` (`SECURITY-REVIEW.md`, `FINDINGS.json`, `GSD-REMEDIATION.md`, `VERIFY-CHECKLIST.md`, `AUDIT-METADATA.md`, `FIXES-APPLIED.md`).
- 34 raw findings → 14 deduped/re-scored: **0 critical, 0 high, 3 medium, 8 low, 3 info**. The prior review's fixes (tenant isolation, CSRF on mutating routes, panel XSS escaping, login `state`, parameterized SQL) were re-verified as holding.
- GSD is not initialized (no `.planning/ROADMAP.md`); the plan advises `/gsd-onboard` before applying phases.

## Fixes applied (verified)

- **SEC-001** desktop [[Desktop tool]] CSRF: `webapp.py` now requires `application/json` + checks `Origin` → blocks cross-site simple-request writes to `config.json`/monitor. (live: text/plain→403, same-origin JSON→200)
- **SEC-002** SSRF: `db.is_blocked_host()` rejects private/loopback/link-local/metadata alarm IPs in `validate_alarm`.
- **SEC-005** session tokens hashed (sha256) at rest in `db.py`; cookie keeps the raw token.
- **SEC-004** `admin.html` gained `esc()` on all interpolations.
- **SEC-007** desktop responses now send `X-Frame-Options`/`nosniff`/CSP.
- **SEC-006** Discord errors no longer echo the exception (could carry the webhook URL) in `app.py`/`monitor.py`.
- **SEC-008** nginx `server_tokens off` + `limit_req` on login/API + HSTS note.
- **SEC-003** `name`/`server` length-capped in `/api/webhook/test`.
- **SEC-009** `core.save_config` uses a per-pid temp file.
- **SEC-012** exact `is_valid:true` line match in `steam.py`; **SEC-013** BASE_URL non-https startup warning.

## Deferred (decision / larger work)

- SEC-006 poll-payload minimization (breaks wizard edit prefill — UX change), SEC-011 CSP `unsafe-inline` removal (template refactor), SEC-003 app-layer rate limiter, SEC-010 session rotation, SEC-014 CI scanning + signed binaries.

## Note

The 34/34 "CONFIRMED" verifier rate was lenient (many were low/info hardening or duplicates); Phase 5 dedup + my own re-scoring produced the 14 above with realistic severities. `/revisar`'s own workflow post-processing had a shape bug returning empty arrays — the journal was the authoritative source.

## Sources

- [OWASP — SSRF](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)
- [OWASP — CSRF](https://owasp.org/www-community/attacks/csrf)
- [MDN — CORS simple requests](https://developer.mozilla.org/docs/Web/HTTP/CORS#simple_requests)
