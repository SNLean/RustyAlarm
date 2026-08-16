# Phase 1: Quality Foundation — Tests, CI & Critical Fix - Context

**Gathered:** 2026-08-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Stand up the project's first automated safety net for the **SaaS service** (`saas/`) and kill the one known crashing defect. Delivers: a `pytest` test suite covering the security-critical and core-logic paths, a GitHub Actions CI that runs tests + supply-chain audits on every change, and a regression test locking the already-applied STAB-01 fix.

In scope: TEST-01 (test suite), STAB-01 (the `import os` fix + its regression test), SEC-014 (CI security scanning).
Out of scope: the deferred security remediations themselves (Phase 2), frontend work (Phase 3), payments (Phase 4), deploy (Phase 5). New app features. Broadening tests to the desktop tool beyond the STAB-01 regression is optional, not required.
</domain>

<decisions>
## Implementation Decisions

### Test framework & harness
- **D-01:** Use `pytest` + `pytest-asyncio` (as REQUIREMENTS pins). Tests live in `tests/`.
- **D-02:** Exercise the FastAPI app in-process via Starlette's `TestClient` (or `httpx.ASGITransport`) — no real network, no live server. — **Reversibility:** reversible.
- **D-03:** Mock `rustplus` in all tests — never hit a live Rust server in CI. Test the monitor's `RustError`/`connect()==False`/dead-socket handling against a fake socket, and test the pure logic (`validate_alarm`, `is_blocked_host`, session hashing, `same_origin`) directly.
- **D-04:** `winsound` is Windows-only and CI runs on Ubuntu — guard/mameparche sound paths so the desktop `save_config`/config tests run on Linux (import already defensive in `core.py`). Skip or mock any sound-playing assertion off-Windows.

### CI (SEC-014)
- **D-05:** GitHub Actions on `push` and `pull_request`, Ubuntu runner: run `pytest`, then `pip-audit`, then a secret scan. Single workflow file `.github/workflows/ci.yml`. — **Reversibility:** reversible.
- **D-06:** Defer PyInstaller binary code-signing (needs a paid code-signing certificate) and requirements hash-pinning — both to backlog, not this phase.

### STAB-01
- **D-07:** The fix is already applied (`import os` added to `core.py`, commit `603ebac`). This phase only adds the **regression test**: `save_config()` writes without `NameError` and the temp file is per-pid.

### Claude's Discretion
- Exact test file layout, fixture design, and secret-scan tool choice (e.g. `gitleaks` action vs a grep-based scan) are left to the planner/executor.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & requirements
- `.planning/ROADMAP.md` — Phase 1 goal & requirement mapping
- `.planning/REQUIREMENTS.md` — TEST-01, STAB-01, SEC-014 acceptance text

### What the tests must cover (source of truth for behaviors)
- `.planning/security-audit/2026-08-15/FIXES-APPLIED.md` — the fixes to lock with tests (SEC-001 CSRF, SEC-002 SSRF, SEC-005 session hash, SEC-007 headers)
- `.planning/security-audit/2026-08-15/VERIFY-CHECKLIST.md` — per-finding verification method → becomes test assertions
- `.planning/codebase/TESTING.md` — current state (no suite yet) and conventions
- `.planning/codebase/CONCERNS.md` — STAB-01 and other flagged debt

### Code under test
- `saas/db.py` (`validate_alarm`, `is_blocked_host`, session hash), `saas/app.py` (`same_origin`, security-headers middleware, routes), `saas/monitor.py` (RustError/reconnect logic), `webapp.py` (`_csrf_ok`, `_send` headers), `core.py` (`save_config`)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The security fixes already have deterministic, testable seams: `db.is_blocked_host()`, `db.validate_alarm()`, `db._hash_token()`, `app.same_origin()`, `webapp.Handler._csrf_ok()`. Most tests are pure-function or TestClient calls.
- Prior ad-hoc verification scripts (in the session scratchpad) already proved these behaviors — port them into `tests/` as real pytest cases.

### Established Patterns
- SaaS uses a module-level singleton `db` connection (SQLite WAL). Tests should point `RUSTALARM_DATA_DIR` at a temp dir so they don't touch the real `saas_data/`.
- Big ints travel as strings across the JS boundary; tests should assert the string round-trip in `alarm_to_client`/`validate_alarm`.

### Integration Points
- CI runs the same `python -m pytest` a developer runs locally; `requirements.txt` + a new `requirements-dev.txt` (or an extra) supplies pytest/pytest-asyncio/pip-audit.
</code_context>

<specifics>
## Specific Ideas

- Tests should be runnable on Ubuntu (matches the deploy target and CI) despite the desktop tool being Windows-only — hence the `winsound` guard decision (D-04).
</specifics>

<deferred>
## Deferred Ideas

- **App-layer rate limiter** — TEST-01 lists "rate-limit thresholds", but rate limiting is currently nginx-only (app-layer deferred as SEC-003 in Phase 2). ⚠ Planner note: either add a minimal, unit-testable app-layer limiter in Phase 2 and put that test there, or scope the Phase 1 rate-limit assertion to "nginx config present". Do not block Phase 1 on it.
- **Binary code-signing** and **requirements hash-pinning** (SEC-014 optional parts) — backlog, need a cert / maintenance decision.
- **Desktop-tool test coverage** beyond the STAB-01 regression — future.

### Reviewed Todos (not folded)
None — no pending todos matched this phase.
</deferred>

---

*Phase: 1-Quality Foundation — Tests, CI & Critical Fix*
*Context gathered: 2026-08-15*
