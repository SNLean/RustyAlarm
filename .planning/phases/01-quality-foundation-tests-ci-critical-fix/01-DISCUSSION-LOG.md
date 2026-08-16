# Phase 1 — Discussion Log

**Date:** 2026-08-15 · Mode: manager-dispatched discuss (owner delegated decisions)

## Areas discussed

### CI scope (SEC-014)
- Options: tests+audits per push/PR · tests only · full (+hash-pin+matrix)
- **Selected:** GitHub Actions on push/PR — pytest + pip-audit + secret-scan (Ubuntu).

### Desktop binary signing (SEC-014 optional)
- Options: defer · include now
- **Selected:** Defer — needs a paid code-signing certificate. Backlog.

## Claude's discretion (owner delegated)
- Test framework/harness: pytest + pytest-asyncio, FastAPI TestClient, mock rustplus, guard winsound on Linux.
- STAB-01 already fixed (commit 603ebac); this phase adds the regression test only.

## Deferred
- App-layer rate limiter (nginx-only for now) → Phase 2 / scope the test there.
- Binary signing, requirements hash-pinning → backlog.
