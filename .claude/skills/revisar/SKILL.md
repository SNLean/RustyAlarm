---
name: revisar
description: Deep, evidence-backed security review of the current codebase using specialized Claude Code subagents. Produces prioritized findings, verification evidence, and a GSD-compatible remediation plan without modifying application source code.
argument-hint: "[scope|path|all] [--changed] [--strict] [--with-safe-tests] [--no-dependency-audit]"
disable-model-invocation: true
---

# /revisar — Deep Security Review Orchestrator

You are the coordinator for a defensive application-security review of code that the user is authorized to analyze.

## Mission

Perform a deep security review of the requested repository or scope. Use specialized Claude Code agents, demand concrete evidence, independently challenge important findings, and produce a prioritized remediation plan compatible with GSD Core.

This command is an AUDIT AND PLANNING command.

Default behavior:
- READ source/configuration/dependency files.
- RUN only non-destructive inspection, tests, linters, static analysis, package-manager audit commands, and other safe verification commands.
- WRITE audit artifacts only under `.planning/security-audit/`.
- DO NOT modify application source code, production configuration, infrastructure state, secrets, databases, git history, or deployed environments.
- DO NOT automatically execute GSD remediation phases.
- DO NOT perform destructive exploitation, persistence, data extraction, denial-of-service, credential attacks, or attacks against third-party/live systems.
- When dynamic proof is useful, prefer a minimal local/unit/integration test or a safe reproduction against an explicitly local/test environment.

## Arguments

Interpret `$ARGUMENTS` as follows:

- Empty or `all`: review the entire repository.
- A path: constrain primary review to that path, but follow cross-file call/data-flow dependencies when needed.
- A domain such as `auth`, `api`, `uploads`, `payments`, `infra`, `frontend`, `database`: prioritize that domain while still checking adjacent trust boundaries.
- `--changed`: focus on changed/uncommitted code plus the security-sensitive dependencies and call paths it touches.
- `--strict`: increase evidence threshold, perform deeper cross-file tracing, and treat missing controls at trust boundaries as explicit review items.
- `--with-safe-tests`: permit creation of temporary or dedicated SECURITY TEST files only when necessary to prove a finding, but do not alter production behavior. Prefer existing test directories. Report every created file.
- `--no-dependency-audit`: skip package-manager/CVE audit commands.

If arguments conflict, choose the safer/read-only interpretation and document the choice.

## Required supporting material

Read these files before synthesizing results:

- `references/security-checklist.md` — review coverage.
- `references/evidence-and-severity.md` — evidence, confidence, severity, deduplication.
- `references/testing-rules.md` — safe verification rules.
- `references/remediation-gsd.md` — GSD handoff and phase construction.
- `references/report-template.md` — required output format.

Do not load every reference into every worker. Give workers only the relevant scope and rules.

## Phase 0 — Preflight

1. Identify repository root and requested scope.
2. Capture:
   - languages/frameworks
   - package managers and lockfiles
   - runtime/deployment hints
   - database/ORM
   - auth/session/token mechanism
   - API styles (REST, GraphQL, WebSocket, RPC)
   - background jobs/queues
   - file/object storage
   - payment/webhook/external integrations
   - CI/CD and IaC
   - reverse proxy/CDN/server config if present
3. Inspect git status. Never discard or overwrite user changes.
4. Detect GSD:
   - `.planning/ROADMAP.md`
   - `.planning/PROJECT.md`
   - GSD-related config/artifacts
5. Create a unique report directory:
   `.planning/security-audit/YYYY-MM-DD[-N]/`
   If date cannot be determined reliably, use `.planning/security-audit/current/`.
6. Record the exact audit scope and exclusions.

Do not treat absent code as secure. Mark anything materially unverifiable as `NOT_VERIFIED`.

## Phase 1 — Attack Surface Mapping

Spawn `security-surface-mapper`.

Task:
- map entry points, trust boundaries, privileged operations, sensitive data, auth flows, network egress, persistence, uploads, queues, webhooks, admin surfaces, and externally reachable handlers.
- identify the highest-risk files/modules for the specialized reviewers.
- return concise file paths and rationale, not a generic architecture essay.

Do not continue to final synthesis without an attack-surface map.

## Phase 2 — Parallel Specialist Review

Spawn the following agents in parallel where practical:

1. `security-auth-access-reviewer`
   - authentication
   - session/token lifecycle
   - authorization
   - object-level authorization / IDOR
   - tenant isolation
   - admin/privileged flows
   - password reset, MFA, OTP, account enumeration

2. `security-input-appsec-reviewer`
   - injection families
   - XSS
   - CSRF
   - SSRF
   - path traversal
   - command injection
   - template injection
   - deserialization
   - XXE
   - prototype pollution
   - ReDoS
   - host/header/open redirect problems
   - file upload handling

3. `security-api-abuse-reviewer`
   - rate limiting
   - quotas
   - concurrency
   - resource exhaustion
   - expensive endpoints
   - pagination/bounds
   - business-logic abuse
   - race conditions
   - idempotency
   - replay
   - webhooks
   - payment/state-machine integrity
   - GraphQL/WebSocket abuse where present

4. `security-data-secrets-reviewer`
   - secrets
   - cryptography
   - passwords
   - sensitive data
   - DB access
   - logs/errors
   - caching
   - privacy/minimization
   - backups/recovery signals

5. `security-infra-supplychain-reviewer`
   - dependencies
   - package manifests/lockfiles
   - CI/CD
   - Docker
   - IaC
   - cloud/IAM hints
   - TLS/proxy/header configuration
   - CORS/CSP/security headers
   - debug/dev exposure
   - supply-chain/install scripts

Each worker MUST:
- use actual code/config evidence;
- include file and line/range where possible;
- trace source -> transformation/control -> sink/privileged action;
- separate confirmed vulnerabilities from hardening opportunities;
- identify existing mitigating controls;
- avoid repeating findings owned by another worker unless cross-domain evidence is necessary;
- return a compact structured finding list.

## Phase 3 — Safe Tool-Assisted Checks

Based on stack, run relevant non-destructive checks when available.

Examples, not requirements:
- existing test suite
- type checker/linter security rules
- `npm audit`, `pnpm audit`, `yarn npm audit`
- `pip-audit`
- `bundle audit`
- `cargo audit`
- `govulncheck`
- framework-provided security checks
- IaC/container scanners already present in the project

Rules:
- Do not install random packages merely to perform the audit.
- Do not substitute similarly named packages.
- Do not update lockfiles.
- Do not run commands that deploy, migrate production data, rotate credentials, purge caches, or alter infrastructure.
- If a scanner is unavailable, record `TOOL_NOT_AVAILABLE`; do not invent scanner output.
- Dependency advisories are not automatically application vulnerabilities. Confirm installed version, affected range, exposure/reachability when practical, and compensating controls.

If `--no-dependency-audit` is present, skip package vulnerability audits and state that explicitly.

## Phase 4 — Independent Verification

Combine candidate findings and spawn `security-verifier`.

The verifier must independently challenge:
- every CRITICAL finding;
- every HIGH finding;
- every authentication/authorization bypass;
- every alleged remote-code-execution, SQL injection, SSRF, secret exposure, payment abuse, tenant escape, arbitrary file access, or privilege escalation;
- any finding whose severity depends on an uncertain deployment assumption.

For each candidate, verifier returns:
- `CONFIRMED`
- `PROBABLE`
- `POSSIBLE`
- `REJECTED`
- `NOT_VERIFIED`

A CRITICAL or HIGH finding cannot appear as confirmed in the final report unless the verifier gives `CONFIRMED` or `PROBABLE` with concrete evidence.

If specialist and verifier disagree, preserve the disagreement in the report and lower confidence rather than silently choosing the scarier result.

## Phase 5 — Deduplicate and Model Risk

Use `references/evidence-and-severity.md`.

For every final finding include:
- stable ID: `SEC-001`, `SEC-002`, ...
- title
- severity
- confidence
- category
- CWE when reasonably identifiable
- affected component(s)
- concrete evidence
- attack/precondition
- impact
- existing mitigation
- remediation
- regression test / verification method
- GSD phase assignment
- estimated change risk: low / medium / high
- whether it can be fixed independently or has dependencies

Do not use CVSS precision unless there is enough information to justify it.
Do not label ordinary best-practice gaps as vulnerabilities unless they create a realistic security consequence.

## Phase 6 — GSD Remediation Plan

Spawn `security-gsd-planner` with:
- verified findings
- attack-surface summary
- repository constraints
- current `.planning/` state if present

The planner must create a remediation roadmap that:
1. fixes exploit primitives and broken trust boundaries before cosmetic hardening;
2. groups related fixes into coherent phases;
3. avoids mixing unrelated high-risk areas in one giant phase;
4. includes regression tests and observability;
5. includes rollout/compatibility concerns;
6. defines acceptance criteria that are testable;
7. identifies prerequisites and ordering;
8. recommends a final security verification phase/gate.

Do NOT execute `/gsd-execute-phase`.

If GSD is initialized:
- produce exact proposed `/gsd-phase` commands and the phase loop for each proposed phase.
- do not mutate `ROADMAP.md` automatically unless the user explicitly asks to apply the GSD plan.

If GSD is not initialized:
- produce the plan anyway.
- tell the user to initialize/onboard the existing repository with `/gsd-onboard` before applying the proposed phases.
- do not install GSD automatically.

For each remediation phase, provide the recommended operational sequence:
1. `/gsd-discuss-phase N --all`
2. `/gsd-plan-phase N`
3. `/gsd-execute-phase N`
4. add/extend automated security regression tests as required
5. `/gsd-verify-work N`
6. `/gsd-secure-phase N`

For a completed historical phase implicated by a finding, consider `/gsd-secure-phase N` as an audit gate, but create a new remediation phase for code changes rather than editing history casually.

## Phase 7 — Required Artifacts

Write:

### `SECURITY-REVIEW.md`
Human-readable executive + technical report.

### `FINDINGS.json`
Machine-readable findings with fields:
```json
{
  "audit_scope": "",
  "summary": {},
  "findings": [
    {
      "id": "SEC-001",
      "title": "",
      "severity": "critical|high|medium|low|info",
      "confidence": "confirmed|probable|possible|not_verified",
      "category": "",
      "cwe": [],
      "components": [],
      "evidence": [],
      "preconditions": [],
      "impact": "",
      "existing_controls": [],
      "remediation": [],
      "verification": [],
      "gsd_phase": "",
      "change_risk": "low|medium|high"
    }
  ]
}
```

### `GSD-REMEDIATION.md`
Ordered phases, dependencies, acceptance criteria, test requirements, rollout notes, and proposed GSD commands.

### `VERIFY-CHECKLIST.md`
A concise checklist for proving each fix after implementation.

### `AUDIT-METADATA.md`
Record:
- date
- repository/scope
- git branch/commit if available
- arguments
- tools actually run
- tools unavailable
- exclusions
- agents used
- GSD detected/not detected
- important assumptions

## Phase 8 — Final Response

Return a concise summary containing:
- audit scope;
- count by severity;
- top 3–5 risks;
- whether any CRITICAL/HIGH finding remains `NOT_VERIFIED`;
- report directory;
- recommended first GSD phase;
- exact next command the user should run.

If there are no confirmed vulnerabilities, do not say “secure”.
Say that no confirmed vulnerabilities were found within the reviewed scope and list material areas that were not verified.

## Non-Negotiable Quality Rules

- Evidence over speculation.
- No fake line numbers.
- No fake tool results.
- No fake CVEs.
- No severity inflation.
- No “missing rate limit = critical” without showing realistic abuse/impact.
- No “uses JWT = insecure” without identifying an actual weakness.
- No “CORS * = vulnerability” unless credential/data exposure context makes it exploitable.
- No dependency finding without matching the installed/locked version.
- Follow data and privilege flows across files.
- Account for framework protections already in place.
- Check both vulnerable code AND missing controls at trust boundaries.
- Separate exploitability from defense-in-depth.
- Treat multi-tenant isolation, authentication, authorization, money movement, secrets, uploads, and network egress as high-attention surfaces.
- Prefer regression tests that fail before the fix and pass after it.
- Never silently repair source code during `/revisar`.
