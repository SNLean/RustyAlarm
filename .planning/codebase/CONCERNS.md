# Codebase Concerns

**Analysis Date:** 2026-08-15

## Critical Bugs

**Missing `os` import in core.py**
- Issue: Line 171 of `core.py` calls `os.getpid()` but the module is never imported. This causes a `NameError` at runtime when `save_config()` is called.
- Files: `core.py:171`
- Impact: SEC-009 (config.json race condition) fix is broken. Calling `save_config()` from `webapp.py:166` or `core.py:166` will crash the application.
- Fix approach: Add `import os` to the imports section of `core.py` (around line 1-14).
- Priority: **CRITICAL** — blocks current functionality

## Tech Debt

### Testing

**No automated test suite**
- Issue: Zero test files found; no test runner (pytest/unittest) configured; no test coverage measurement.
- Files: Project root has no `tests/`, `test_*.py`, or `*_test.py` files.
- Impact: Code changes have no regression detection. State management logic (async monitor, database transactions, CSRF validation) is unverified. Security fixes (SEC-001 through SEC-009) have no automated verification.
- Fix approach: Add pytest as dev dependency. Create test structure:
  - `tests/unit/` for isolated function tests (validation, config, helpers)
  - `tests/integration/` for DB + monitor interactions
  - `tests/e2e/` for HTTP endpoints (using TestClient)
  - Minimum target: 70% line coverage on critical paths (db.py, monitor.py, app.py)
- Priority: **HIGH** — foundational quality gap

### Concurrency & State Management

**Thread-unsafe logging in AlarmMonitor and AlarmRunner**
- Issue: `AlarmMonitor.logs` (core.py:210) and `AlarmRunner.logs` (monitor.py:57) are deques written to without locks. Concurrent reads (via `logs_since()` in webapp.py:237-239 / `snapshot()` in monitor.py:67-76) can miss or duplicate entries.
- Files: `core.py:210-239`, `saas/monitor.py:57-76`
- Impact: Lost or corrupted log entries during concurrent access; frontend may see gaps in real-time monitor logs.
- Fix approach: Use `threading.Lock()` in `AlarmMonitor` and `asyncio.Lock()` in `AlarmRunner` to protect log access.
- Priority: **MEDIUM** — occurs only under high concurrency (multiple simultaneous API calls to monitor)

**Single-worker constraint for SaaS monitor**
- Issue: The `Manager` class in `saas/monitor.py` maintains in-memory state (`self.runners: dict[int, AlarmRunner]`). If the SaaS is deployed with multiple workers (e.g., `gunicorn -w 4`), each worker has its own `Manager` instance with separate alarms. Sync becomes inconsistent.
- Files: `saas/monitor.py:217-277`, `saas/__main__.py` (uvicorn startup)
- Impact: Only one worker actually monitors alarms; others hold stale state. Load balancing breaks alarm monitoring. Scaling horizontally is impossible.
- Fix approach: Move alarm state to a shared store (Redis, DB-backed queue, or a dedicated monitor microservice). Current single-worker deployment is undocumented.
- Priority: **HIGH** — blocks horizontal scaling; should be documented as a deployment constraint

### Fragile Dependencies

**Rustplus logger handler accumulation workaround**
- Issue: The rustplus library (6.0.9) adds a StreamHandler on every `RustSocket()` initialization without cleanup. The code calls `quiet_rustplus_logger()` (monitor.py:28-37) after every socket construction to clear handlers. This is a fragile workaround for a library bug.
- Files: `saas/monitor.py:28-40, 109`
- Evidence: Comment on lines 29-32 describes it as a memory leak + log duplication risk ("se acumulan sin techo").
- Impact: If rustplus behavior changes or the workaround is forgotten, handlers accumulate → memory leak + log spam.
- Fix approach: Either (1) patch rustplus upstream to not add handlers by default, or (2) upgrade to a fixed version when available, or (3) document this as a known workaround and check periodically for rustplus updates.
- Priority: **MEDIUM** — latent risk, not active issue at current scale

### Performance & Scalability

**SQLite scalability limit**
- Issue: The application uses SQLite with WAL mode and a global lock (`saas/db.py:18`). The code comment (line 2) acknowledges "A esta escala sqlite3 en WAL con un lock alcanza de sobra" — it works for "decenas de usuarios" (tens of users) but will bottleneck as the user base grows.
- Files: `saas/db.py:1-84`
- Impact: Write contention on the lock; all DB operations serialize through `_run()`. At 100+ concurrent users or high-frequency polling, latency increases.
- Fix approach: No immediate action needed, but document a migration plan to PostgreSQL when user count exceeds 50-100. Set up query performance monitoring now.
- Priority: **LOW** — not an immediate problem; deferred until scale requires it

**No database backups or recovery mechanism**
- Issue: The database file `saas_data/rustalarm.db` has no backup, replication, or recovery procedure. Data loss (disk failure, accidental deletion, corruption) is permanent.
- Files: `saas/config.py:24`, deployment scripts (none)
- Impact: Loss of all user accounts, alarm configurations, and session history.
- Fix approach: Add automated daily backups to cloud storage (S3, GCS, etc.). Document recovery procedure in DEPLOY.md.
- Priority: **MEDIUM** — critical for production but currently missing

### Missing Features

**No payment processing integration**
- Issue: The `users.plan_active` field exists in the schema (saas/db.py:26) and is checked in authorization (app.py:209), but there is no payment processor integrated. Only the admin can manually toggle `plan_active` via `/api/admin/users/{steam_id}/toggle`.
- Files: `saas/db.py:121-123`, `saas/app.py:339-351`
- Impact: SaaS model cannot be monetized. No way to enforce trial limits, subscription enforcement, or payment collection.
- Fix approach: Integrate a payment provider (Stripe, Paddle, etc.). Implement a pricing page, checkout flow, webhook for subscription status updates, and automated plan_active sync.
- Priority: **LOW** — business feature, not a technical issue; deferred until SaaS launch

**No error retry for Discord webhook delivery**
- Issue: When `send_discord()` fails (e.g., transient Discord API error), the exception is caught and logged once. The notification is lost forever — there is no retry queue or dead-letter mechanism.
- Files: `saas/monitor.py:200-214`, `saas/app.py:291-300`
- Impact: Alarm notifications are silently dropped if Discord is temporarily unavailable. Users miss critical alerts.
- Fix approach: Implement a persistent retry queue (in DB or message broker). Store failed sends, retry with exponential backoff, eventually dead-letter after max retries.
- Priority: **MEDIUM** — impacts alarm reliability; affects SaaS usability

### Hardcoded Parameters

**Non-configurable polling and retry parameters in monitor.py**
- Issue: Key tuning parameters are hardcoded:
  - `SYNC_INTERVAL = 30` (manager resync frequency)
  - `RETRY_BASE = 15` (initial reconnect backoff)
  - `RETRY_MAX = 300` (max backoff, 5 minutes)
  - `MIN_INTERVAL = 2` (minimum check interval)
  - `RECONNECT_AFTER = 8` (unhealthy response threshold)
- Files: `saas/monitor.py:21-25`
- Impact: Cannot tune performance or resilience for different deployment scenarios without code changes.
- Fix approach: Move to environment variables (e.g., `RUSTALARM_RETRY_BASE`) in `saas/config.py`, with defaults matching current values.
- Priority: **LOW** — nice-to-have for operations; not blocking

### Input Validation

**Inconsistent field length limits**
- Issue: Field length capping is inconsistent:
  - Alarm name: capped at 60 chars (saas/db.py:204)
  - Server in webhook test: capped at 100 chars (saas/app.py:319)
  - Player token and entity ID: parsed as integers but no length validation in form (though bounds checked against int32)
  - Discord webhook: not explicitly length-capped (validation only checks prefix)
- Files: `saas/db.py:198-264`, `saas/app.py:304-326`
- Impact: No security impact (values are already escaped before rendering), but inconsistent UX. Form field maxlen should match server validation.
- Fix approach: Define a constants file (`MAX_NAME_LEN = 60`, `MAX_SERVER_LEN = 100`, etc.) and enforce symmetrically on client and server.
- Priority: **LOW** — UX polish; no functional impact

### Rate Limiting

**Partial rate limiting (SEC-003)**
- Issue: Nginx `limit_req` is configured (deploy/nginx.conf) for `/login`, `/auth/steam/return`, and `/api/`, but there is no app-layer fallback. If nginx is bypassed (local deployment, misconfiguration, reverse proxy removal), the app has no rate limiting.
- Files: `deploy/nginx.conf`, `saas/app.py:151-176, 294-314`
- Impact: Unthrottled session creation, webhook-test spam, and auth return amplification if nginx is absent.
- Fix approach: Add an in-app per-session/IP rate limiter (e.g., using `slowapi` or `ratelimit`). Nginx remains the primary defense; app layer is backup.
- Priority: **MEDIUM** — deferred in SEC-003 but should be implemented for defense-in-depth

### Secrets Exposure (SEC-006 Partial)

**Discord webhook and player token streamed in polling response**
- Issue: The `/api/alarms` poll response (called every 2 seconds by the client) includes the raw `discord_webhook` URL and `player_token` (saas/app.py:90-101). These secrets are continuously held in the browser's DOM/JS memory.
- Files: `saas/app.py:90-106`
- Impact: Longer attack surface for credential theft (if browser is compromised). Webhook URL also leaks into error messages (SEC-006 partially mitigated by removing exception echo, but structure remains).
- Fix approach: Send a boolean `has_webhook` instead of the URL in the poll response. Fetch the full webhook URL only when the user opens the edit dialog (separate endpoint, if needed). Requires UX change to disable prefill.
- Priority: **MEDIUM** — deferred in SEC-006 as UX decision; should be re-evaluated

### Deployment & CI/CD (SEC-014)

**No CI/CD security scanning or binary signing**
- Issue: No GitHub Actions or CI pipeline. PyInstaller binaries (`webapp.spec`, `rust.spec`) are unsigned. Dependencies are pinned by version but not by hash.
- Files: Project root (no `.github/workflows/`), `requirements.txt`
- Impact: No automated vulnerability scanning. Unsigned binaries can be spoofed or tampered with. Transitive dependency vulnerabilities not detected automatically.
- Fix approach: Add GitHub Actions workflow to run `pip-audit`, `bandit`, and `semgrep` on PRs. Implement PyInstaller code signing (Windows Authenticode or macOS notarization). Consider hash-pinned requirements with `pip-compile`.
- Priority: **MEDIUM** — best practice for supply chain security; deferred

## Fragile Areas

### Desktop Panel Configuration Save

**Race condition in config.json handling (SEC-009 fixed, but buggy)**
- Issue: `core.py:save_config()` was fixed to use unique temp filenames per process (SEC-009). However, the import of `os` is missing, so `os.getpid()` will fail.
- Files: `core.py:166-176` (implementation), `webapp.py:152-159` (caller)
- Impact: Config save crashes the application (NameError).
- Fix approach: Add `import os` to `core.py`.
- Priority: **CRITICAL** (see Critical Bugs section)

### Steam OpenID Verification

**Loose substring matching for OpenID response**
- Issue: SEC-012 was partially fixed. The original substring match was changed to exact-line matching. However, if Steam's OpenID response format changes or returns extra text, the match could fail silently.
- Files: `saas/steam.py:54-58`
- Impact: Login fails silently if OpenID format changes. No indication of version mismatch.
- Fix approach: Parse the response more robustly (use a proper config parser or regex with capture groups). Log a warning if the response format is unexpected.
- Priority: **LOW** — Steam is stable; low risk

### Alarm Entity ID Validation

**Entity ID from untrusted database**
- Issue: `saas/monitor.py:146` calls `await socket.get_entity_info(row["entity_id"])`. The entity_id comes from the DB as an integer but is trusted without re-validation. If someone directly modifies the DB or exploits a past injection, an invalid entity_id could cause crashes.
- Files: `saas/monitor.py:145-146`, `saas/db.py:283-301`
- Impact: Alarm runner crashes on invalid entity_id; user sees "error" status with cryptic Rust+ message.
- Fix approach: Re-validate entity_id in `AlarmRunner._session()` before calling socket. Log a clear error if out of range.
- Priority: **LOW** — already bounded by int32 in DB; unlikely to happen

## Missing Error Recovery

**No graceful degradation for missing sound file**
- Issue: `core.py:play_sound()` raises `FileNotFoundError` if `alarma.wav` is missing. The caller (monitor.py:375) catches it and logs a warning, but the alarm still plays (or fails silently).
- Files: `core.py:187`, `saas/monitor.py:185` (monitor context is different), `webapp.py:181-186`
- Impact: If `alarma.wav` is deleted, alarm notifications in desktop mode stop working without clear indication.
- Fix approach: Check for sound file existence at startup. Provide a default beep via the `winsound` module as fallback.
- Priority: **LOW** — edge case; user can manually fix

## Known Deferred Security Fixes

These items are already identified in the security audit but deferred:

| Finding | Status | Reason |
|---------|--------|--------|
| SEC-003 (app-layer rate limiter) | Partial | nginx handles it; per-endpoint limiter design pending |
| SEC-006 (poll payload minimization) | Partial | Error redaction done; webhook/token hiding needs UX change |
| SEC-010 (session rotation & idle timeout) | Deferred | Optional hardening; current 30-day expiry sufficient |
| SEC-011 (CSP unsafe-inline removal) | Deferred | Requires template refactor to move inline JS to files + nonces (high change risk) |
| SEC-014 (CI security scanning & signed binaries) | Deferred | Process/infra; not code |

## Monitoring & Observability

**No structured logging or monitoring**
- Issue: Logs are unstructured strings in in-memory deques. No centralized log aggregation, no metrics collection, no alerting.
- Files: `core.py:223-239`, `saas/monitor.py:60-65`, `saas/app.py` (uses Python's logging module minimally)
- Impact: Difficult to diagnose issues in production. No visibility into alarm success/failure rates or system health.
- Fix approach: Integrate structured logging (Python `structlog` or similar) and send to a log aggregation service (e.g., ELK, Datadog, CloudWatch). Expose Prometheus metrics for uptime/trigger counts.
- Priority: **LOW** — nice-to-have for ops; not blocking MVP

---

*Concerns audit: 2026-08-15*
