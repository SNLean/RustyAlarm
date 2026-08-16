# Audit metadata

- **Date:** 2026-08-15
- **Repository / scope:** RustyAlarm; entire application code (`saas/`, desktop tool, `deploy/`, dependencies). Excluded: `skills/` (vendored), `.claude/` (audit tooling), `docs/` (vault), `dist/`, `build/`, `.history/`, `saas_data/`, `__pycache__/`.
- **Git:** branch `main`, commit `b327897`, working tree clean at audit start.
- **Arguments:** `analiza todo mi codigo en busqueda de bulneravilidades y fixealas` → interpreted as full-repo review. The "fixealas" (fix) part is out of `/revisar`'s audit-only contract; fixes are applied as a separate, explicitly-approved step after this audit.
- **Tools run:** `pip-audit -r requirements.txt` (clean); FastAPI static review; git inspection.
- **Tools unavailable (`TOOL_NOT_AVAILABLE`):** no CI/container/IaC scanners in the project; no lockfile with hashes for full transitive CVE reachability.
- **Agents used:** security-surface-mapper (1), 5 domain specialists (auth-access, input-appsec, api-abuse, data-secrets, infra-supplychain), per-finding adversarial verifiers — 40 agents total via the review workflow.
- **GSD detected:** No (`.planning/` absent). Plan advises `/gsd-onboard` before applying phases.
- **Findings:** 34 raw → 14 after dedup/re-score. critical 0 · high 0 · medium 3 · low 8 · info 3.
- **Key assumptions:** deployment behind nginx + TLS per `deploy/`; single uvicorn worker (documented invariant); Rust+ servers are public game servers (so blocking private ranges for alarm IPs does not break legitimate use).
- **Note:** much of `saas/` was hardened in an earlier same-session review; those fixes were re-verified as still present (tenant isolation, CSRF on mutating routes, panel XSS escaping, login `state`, parameterized SQL, env-only admin).
