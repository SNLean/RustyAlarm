# Verify checklist — RustyAlarm remediation

One check per finding. Tick after the fix.

- [ ] **SEC-001** Cross-site `text/plain` POST to `http://127.0.0.1:8765/api/config` returns 403; same-origin JSON POST from the panel still saves.
- [ ] **SEC-002** `POST /api/alarms` with `ip=127.0.0.1` and with `ip=169.254.169.254` return a validation error; a public IP still works.
- [ ] **SEC-003** Repeated `POST /api/webhook/test` past the threshold returns 429; overlong `name`/`server` rejected; nginx `limit_req` present in config.
- [ ] **SEC-004** Every interpolation in `admin.html` passes through `esc()`; an injected `<img onerror>` in a rendered field would render as text.
- [ ] **SEC-005** `sessions` table stores only token hashes; login, `/api/alarms`, and logout still work.
- [ ] **SEC-006** A forced Discord failure produces a client/log message with no webhook URL in it.
- [ ] **SEC-007** Desktop panel responses carry `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and a CSP.
- [ ] **SEC-008** `server_tokens off;` present; HSTS in the 443 block after certbot.
- [ ] **SEC-009** Two concurrent desktop config saves do not corrupt `config.json`.
- [ ] **SEC-010** (if adopted) session cap/idle policy behaves as specified.
- [ ] **SEC-011** (deferred) CSP without `unsafe-inline` and the app still functions.
- [ ] **SEC-012** Steam `is_valid:true` matched as an exact line; login still works.
- [ ] **SEC-013** Startup warns when `RUSTALARM_BASE_URL` is non-https and host is not localhost.
- [ ] **SEC-014** CI runs `pip-audit` + secret scan; release process documented.
