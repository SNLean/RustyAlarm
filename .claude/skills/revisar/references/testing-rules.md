# Safe verification rules

`/revisar` is an audit. Verification must never change application behavior, data, or infrastructure.

## Always allowed (read-only / non-destructive)

- Read source, config, dependency manifests, lockfiles.
- `grep`/search, static analysis, type checkers, linters (report-only).
- Run the **existing** test suite if it is safe and hermetic.
- Package-manager audit commands that only read advisories:
  - Node: `npm audit`, `pnpm audit`, `yarn npm audit`
  - Python: `pip-audit`
  - Ruby: `bundle audit`
  - Rust: `cargo audit`
  - Go: `govulncheck`
- Framework-provided security checks and any scanner **already present** in the project.
- `git status` / read-only git inspection (never discard or overwrite user changes).

## Never do

- Install packages just to run the audit; substitute similarly named packages; update lockfiles.
- Deploy, migrate production data, rotate credentials, purge caches, or alter infrastructure.
- Destructive exploitation, persistence, data extraction, DoS, credential attacks, or anything against third-party/live systems.
- Modify application source, production config, secrets, databases, git history, or deployed environments.

## Dynamic proof

When a static trace is not enough, prefer the smallest safe reproduction:

- A local unit/integration test, or a run against an explicitly **local/test** environment only.
- Only create test files when `--with-safe-tests` is set; prefer existing test dirs; do not alter production behavior; **report every file created**.
- A regression test that fails before the fix and passes after it is the gold standard.

## Honesty about tooling

- If a scanner is unavailable, record `TOOL_NOT_AVAILABLE`. Never invent scanner output, CVEs, or line numbers.
- A dependency advisory is not automatically an application vulnerability. Before reporting: confirm the **installed/locked** version is in the affected range, check whether the vulnerable code path is reachable, and note compensating controls.
- With `--no-dependency-audit`, skip package vulnerability audits and say so explicitly in the report.

If arguments or conditions conflict, choose the safer/read-only interpretation and document the choice.
