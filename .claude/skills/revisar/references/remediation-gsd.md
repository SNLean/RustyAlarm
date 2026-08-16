# GSD handoff and phase construction

How verified findings become a GSD Core remediation roadmap. `/revisar` plans; it never executes GSD phases.

## Ordering principles

1. **Fix exploit primitives and broken trust boundaries first** — auth/authz bypass, injection, SSRF, secret exposure, tenant escape — before cosmetic hardening.
2. **Group related fixes** into one coherent phase (same subsystem / same root cause family).
3. **Do not mix** unrelated high-risk areas in one giant phase.
4. Each phase carries **regression tests** and any needed **observability**.
5. Account for **rollout/compatibility** (sessions, tokens, migrations, clients).
6. Define **testable acceptance criteria**.
7. State **prerequisites and ordering** between phases.
8. End with a **final security verification** phase/gate.

## Phase shape

For each remediation phase record: goal, findings covered (`SEC-xxx`), files/areas touched, dependencies/order, acceptance criteria, required tests, rollout notes, and change risk.

## GSD detected (`.planning/` present)

Produce exact proposed commands per phase; do **not** mutate `ROADMAP.md` unless the user explicitly asks to apply the plan. Recommended loop per phase N:

1. `/gsd-discuss-phase N --all`
2. `/gsd-plan-phase N`
3. `/gsd-execute-phase N`
4. add/extend automated security regression tests
5. `/gsd-verify-work N`
6. `/gsd-secure-phase N`

For a completed historical phase implicated by a finding, use `/gsd-secure-phase N` as an audit gate, but create a **new** remediation phase for code changes rather than editing history.

## GSD not initialized

Produce the plan anyway. Tell the user to run `/gsd-onboard` to onboard the existing repo before applying the phases. Do not install or initialize GSD automatically.

## Guardrails

- Never execute `/gsd-execute-phase` from within `/revisar`.
- Never silently repair source during the audit.
- Prefer regression tests that fail before the fix and pass after.
