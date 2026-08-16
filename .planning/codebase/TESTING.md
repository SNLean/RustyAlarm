# Testing Patterns

**Analysis Date:** 2026-08-15

## Overview

**Status: No Automated Test Suite**

This repository contains **no automated tests**. There are no test files, no test framework configured, and no CI/CD test jobs.

- No `test/` or `tests/` directory
- No `*_test.py` or `*_spec.py` files
- No `pytest.ini`, `setup.cfg`, or `pyproject.toml` with test configuration
- No `conftest.py` or test fixtures
- No test runner in `requirements.txt` (pytest, unittest, nose, etc.)

This applies to both code paths:
- Desktop tool: `core.py`, `rust.py`, `webapp.py`
- SaaS service: `saas/` FastAPI application

## Testing Strategy (Current)

**Manual Testing:**
- The codebase relies on manual testing only
- End-to-end testing through UI (`webapp.py` web interface for desktop, browser tests for SaaS)
- Command-line testing in `rust.py` mode

**Critical Functions Without Tests:**
- Core validation logic in `core.py:validate_config()` (line 97-150)
- Alarm data validation in `saas/db.py:validate_alarm()` (line 198-264)
- Security-critical SSRF protection in `saas/db.py:is_blocked_host()` (line 182-195)
- Authentication flow in `saas/steam.py:verify()` (line 39-64)
- Alarm monitoring/trigger logic in `core.py:AlarmMonitor._run()` (line 313-396) and `saas/monitor.py:AlarmRunner._session()` (line 101-198)

## Areas Needing Test Coverage

### Validation Logic

**`core.py:validate_config()` (line 97-150):**
- Port range validation: should accept 1-65535, reject 0 and 65536+
- Steam ID, Player Token, Entity ID: integer parsing, range checks
- Interval/Cooldown: float parsing, minimum thresholds
- Error collection: all errors reported together, not early exit
- Normalization: values cleaned and bounds-checked

**`saas/db.py:validate_alarm()` (line 198-264):**
- IP/hostname validation: character whitelist, length limits
- SSRF protection: blocks private/loopback/link-local/reserved/multicast addresses, checks `.local` and `.internal` suffixes
- Port validation: must be 1-65535
- Discord webhook validation: must match expected URL prefixes
- Large integer handling: values must fit in signed 32-bit range (-2,147,483,648 to 2,147,483,647)
- All errors collected and raised together

### Security Validation

**SSRF Protection (`saas/db.py:is_blocked_host()`, line 182-195):**
- Should block: `127.0.0.1`, `localhost`, `0.0.0.0`, `::`, all private IP ranges, link-local, reserved, unspecified, multicast
- Should allow: public IPs (verified by `ipaddress` module)
- Should block: hostnames ending in `.local` or `.internal`
- Should allow: normal domain names

**CSRF Protection (`webapp.py:_csrf_ok()`, line 89-103 and `saas/app.py:same_origin()`, line 76-83):**
- Local panel: checks Host header, requires `application/json` Content-Type for POST
- SaaS: verifies Origin/Referer matches expected scheme + netloc
- State validation in OAuth flow: `saas/app.py:160-169`

**Cookie Security (`saas/db.py:_hash_token()`, line 128-131):**
- Session tokens hashed in database, not stored in plaintext
- Hash is SHA256 of token

### State Management

**Alarm Monitor (`core.py:AlarmMonitor`, line 198-396):**
- Thread-safe state access under `self._lock` (RLock)
- Cooldown logic: should not trigger twice within cooldown window
- Last-trigger timestamp uses `time.monotonic()` (not affected by clock adjustments)
- Thread lifecycle: start(), stop(), running property
- Log buffering: recent 300 entries in deque

**SaaS Alarm Runner (`saas/monitor.py:AlarmRunner`, line 43-214):**
- Async task cancellation and cleanup
- Backoff logic: starts at `RETRY_BASE`, doubles each failure, caps at `RETRY_MAX`, resets on success
- Reconnection after N consecutive failures: `RECONNECT_AFTER` failures trigger reconnect
- Alarm detection: OFF→ON transition triggers notification (with cooldown check)
- Discord notification error handling: catches exceptions, logs without exposing webhook URL

**Manager Sync (`saas/monitor.py:Manager.sync()`, line 243-263):**
- Reconciliation: database alarms vs. running tasks
- Stops tasks for: deleted alarms, disabled alarms, plan inactive
- Starts tasks for: new alarms
- Restarts tasks: if `updated_at` timestamp changed
- Thread-safe under `asyncio.Lock()`

### Integration Points

**Discord Webhook (`saas/notify.py:send_discord()`, line 11-36):**
- Timeout handling: 10-second timeout
- Response status validation: raises on non-2xx
- Embed structure: title, description, color, fields, timestamp

**Steam OpenID (`saas/steam.py`, line 1-64):**
- OAuth state generation and validation: `secrets.token_urlsafe(24)` for state, constant-time comparison in verify
- Claimed ID parsing: must match regex `^https?://steamcommunity\.com/openid/id/(\d{17})$`
- Response validation: checks for `is_valid:true` line (exact match, not substring)

### Database Operations

**Database Concurrency (`saas/db.py`, line 73-84 `_run()` function):**
- All queries protected by module-level RLock
- Foreign key constraints enabled: `PRAGMA foreign_keys=ON`
- WAL mode enabled for concurrent access: `PRAGMA journal_mode=WAL`
- Session cleanup: expired sessions deleted on `create_session()`
- Index usage: queries rely on indexes on `alarms(steam_id)` and `sessions(expires_at)`

## Test Infrastructure Gaps

**Missing Fixtures/Factories:**
- No test database setup (`conftest.py` or fixtures module)
- No mock objects for RustSocket, Discord API, Steam API
- No test data builders or factory patterns

**Missing Mocks:**
- `rustplus.RustSocket` and `ServerDetails` — needed for alarm monitoring tests
- `httpx.AsyncClient` — needed for Discord/Steam API tests
- `sqlite3` connection/cursor — needed for database tests
- System modules (`winsound`) — already has try-except for ImportError

**Missing Test Utilities:**
- No helpers for creating test config/alarm rows
- No assertion helpers for log entry validation
- No async test utilities for running async code in tests

## How to Add Tests

**Recommended approach (if tests are added):**
1. Create `tests/` directory at project root
2. Use `pytest` + `pytest-asyncio` for async test support
3. Use `unittest.mock` for mocking RustSocket, httpx, sqlite3
4. Test files: `tests/test_validate.py`, `tests/test_security.py`, `tests/test_monitor.py`, etc.
5. Use pytest fixtures for shared setup (test database, mock sockets)

**High-Priority Areas to Test First:**
1. Validation logic (high impact, deterministic, easy to test)
2. Security checks (SSRF, CSRF — could cause real damage if broken)
3. Alarm trigger logic and cooldown (core business logic)
4. Database operations and concurrency (data integrity)

**Integration Test Approach:**
- Real RustSocket connection to test Rust+ integration (requires live server or mock)
- Real Discord webhook tests (requires test webhook URL)
- SQLite database tests (can use `:memory:` database)

---

*Testing analysis: 2026-08-15*
