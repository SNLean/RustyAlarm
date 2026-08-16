# GSD remediation plan — RustyAlarm

GSD is **not initialized** in this repo (no `.planning/ROADMAP.md`). To apply these phases with GSD, run `/gsd-onboard` first. The plan stands on its own regardless.

Ordering: fix exploit primitives and broken trust boundaries first, then abuse/exposure, then hardening. No CRITICAL/HIGH exist, so phases are moderate.

## Phase 1 — Trust boundaries & injection sinks (SEC-001, SEC-002, SEC-004, SEC-007)

- **Goal:** close the cross-site and SSRF boundaries and the latent XSS sink.
- **Changes:** desktop CSRF/Origin check + require JSON content-type (SEC-001); private/loopback/link-local blocklist in `validate_alarm` (SEC-002); `esc()` in `admin.html` (SEC-004); security headers on desktop responses (SEC-007).
- **Acceptance:** cross-site text/plain POST to desktop `/api/config` → 403; alarm with ip=127.0.0.1/169.254.169.254 rejected; admin values escaped; desktop responses carry X-Frame-Options/nosniff/CSP.
- **Tests:** regression for the CSRF reject, the SSRF reject, and header presence.
- **Change risk:** low. **Rollout:** none (no data migration).

## Phase 2 — Abuse limits & secret handling (SEC-003, SEC-005, SEC-006)

- **Goal:** throttle abuse-prone endpoints and reduce secret exposure.
- **Changes:** nginx `limit_req` + a lightweight in-app limiter on `/api/webhook/test`, `/auth/steam/return`, alarm create; cap name/server length (SEC-003); hash session tokens at rest (SEC-005); stop reflecting the webhook URL in error/log text, optionally minimize the poll payload (SEC-006).
- **Acceptance:** rapid `/api/webhook/test` returns 429; sessions table stores only hashes and login still works; Discord failure messages contain no webhook URL.
- **Tests:** rate-limit threshold test; session hash round-trip; error-message redaction test.
- **Change risk:** medium (session-store change touches every login — see rollout).
- **Rollout:** hashing existing tokens invalidates current sessions on deploy (users re-login once) — acceptable; announce or deploy off-peak.

## Phase 3 — Hardening & process (SEC-008…SEC-014)

- **Goal:** headers, config guards, and supply-chain process.
- **Changes:** `server_tokens off` + HSTS (SEC-008); unique temp name for desktop config save (SEC-009); session rotation/idle policy (SEC-010); BASE_URL startup guard (SEC-013); exact Steam `is_valid` line parse (SEC-012); CI with `pip-audit`+secret scan, consider hash-pinned requirements and signed binaries (SEC-014). CSP `unsafe-inline` removal (SEC-011) is a larger refactor — schedule separately.
- **Acceptance:** headers present on HTTPS; startup warns on misconfig; CI runs the scans.
- **Change risk:** low, except SEC-011 (high — template refactor).

## Proposed GSD command loop (after `/gsd-onboard`)

Per phase N:
1. `/gsd-discuss-phase N --all`
2. `/gsd-plan-phase N`
3. `/gsd-execute-phase N`
4. add/extend automated security regression tests
5. `/gsd-verify-work N`
6. `/gsd-secure-phase N`

End with a final `/gsd-secure-phase` gate over the whole remediation.
