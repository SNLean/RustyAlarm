# Security review checklist

Coverage map for `/revisar`. Give each specialist only its own section plus the shared rules. Absence of code is not proof of safety — mark unverifiable controls `NOT_VERIFIED`.

## 0 · Attack surface (surface mapper)

- Entry points: HTTP routes, CLI, background jobs, queues, webhooks, sockets, scheduled tasks.
- Trust boundaries: unauthenticated → authenticated, user → admin, tenant → tenant, app → DB/OS/network.
- Privileged operations: money movement, account changes, deletes, config/flag changes, impersonation.
- Sensitive data: credentials, tokens, PII, payment data, secrets, session material.
- Network egress: outbound HTTP, webhooks, SSRF-reachable fetchers.
- Persistence & storage: DB, cache, file/object storage, uploads.
- Externally reachable handlers vs internal-only.
- Output: ranked list of highest-risk files/modules with a one-line rationale each.

## 1 · Authentication & access (auth-access-reviewer)

- Authentication mechanism soundness; credential/token verification actually enforced.
- Session/token lifecycle: creation, rotation, expiry, revocation, fixation, replay.
- Authorization on every privileged route (not just the UI).
- Object-level authorization / IDOR: is every record access scoped to the caller?
- Tenant isolation: can user A read/mutate user B's data?
- Admin/privileged flow gating.
- Password reset, MFA/OTP, account enumeration, login CSRF, open redirect on auth return.

## 2 · Input & appsec (input-appsec-reviewer)

- Injection: SQL/NoSQL/ORM, command, template (SSTI), LDAP, header.
- XSS: reflected, stored, DOM; `innerHTML`/template autoescaping bypass.
- CSRF on state-changing routes; SameSite + token/origin checks.
- SSRF in any server-side fetch; allowlist vs user-controlled URL/host.
- Path traversal / arbitrary file read-write; upload handling and content-type/path.
- Deserialization, XXE, prototype pollution, ReDoS.
- Host/`Host`-header/forwarded-header trust; open redirect.

## 3 · API abuse & business logic (api-abuse-reviewer)

- Rate limiting, quotas, and per-actor caps on expensive/authless endpoints.
- Concurrency and race conditions (TOCTOU) on balances, credits, uniqueness.
- Resource exhaustion: unbounded pagination, large payloads, fan-out.
- Idempotency and replay on payments/webhooks/state machines.
- Webhook authenticity (signature/secret) and side effects.
- Business-logic invariants: can a state be reached out of order?

## 4 · Data & secrets (data-secrets-reviewer)

- Hardcoded secrets, keys, tokens in code/config/history-adjacent files.
- Cryptography: algorithm/mode/IV/salt, password hashing (bcrypt/argon2 vs raw/md5).
- Sensitive data in logs, error responses, caches, backups.
- DB access patterns; least privilege; parameterization.
- Privacy/minimization: is more collected/returned than needed?

## 5 · Infra & supply chain (infra-supplychain-reviewer)

- Dependencies vs installed/locked versions; known-vuln ranges; reachability.
- CI/CD secrets, permissions, untrusted-input build steps, install scripts.
- Docker/IaC/cloud IAM hints; over-broad permissions.
- TLS/proxy config; CORS, CSP, `X-Frame-Options`, `X-Content-Type-Options`, HSTS.
- Debug/dev endpoints, stack traces, source maps, admin panels exposed in prod.

## Shared rules (all workers)

- Cite `file:line` (or a tight range). Trace source → control/transform → sink/privileged action.
- Separate **confirmed vulnerabilities** from **hardening opportunities**.
- Name existing mitigating controls and framework protections.
- Do not repeat a finding owned by another domain unless cross-domain evidence is needed.
- No fabricated line numbers, CVEs, or tool output. See [[evidence-and-severity]] and [[testing-rules]].
