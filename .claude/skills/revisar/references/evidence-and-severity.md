# Evidence, confidence, severity, deduplication

The scoring contract for `/revisar`. Every finding is judged against this. Evidence over speculation, always.

## Evidence requirements

A finding must carry concrete evidence:

- **Location**: `path:line` or a tight line range for both the source (attacker-controlled input) and the sink (dangerous operation).
- **Flow**: the trace source → transformation/control → sink/privileged action, across files if needed.
- **Reachability**: is the code path reachable by the stated actor at the stated trust boundary?
- **Proof strength**, best to weakest: a failing regression/PoC test → a precise code trace → a pattern match needing assumptions.

No evidence, no finding. If a control cannot be located and cannot be proven absent, mark it `NOT_VERIFIED` rather than guessing.

## Confidence

| Level | Meaning |
|---|---|
| `confirmed` | Direct evidence the issue is exploitable/observable as described (trace complete or PoC/test). |
| `probable` | Strong code evidence; a small, realistic assumption remains (e.g., a common deployment default). |
| `possible` | Plausible from the code but depends on unverified context or config. |
| `not_verified` | Could not be checked (missing code/config/tooling). State what is needed to verify. |

A `critical` or `high` finding may appear as confirmed in the report **only** if the verifier returns `CONFIRMED` or `PROBABLE` with concrete evidence. If specialist and verifier disagree, keep both views and lower confidence — never silently pick the scarier one.

## Severity

Judge realistic impact × exploitability at the actual trust boundary, accounting for existing controls.

| Severity | Bar |
|---|---|
| `critical` | Unauthenticated (or trivially authenticated) path to RCE, full auth/authz bypass, mass data exposure, tenant escape, direct money theft, secret leak enabling the above. |
| `high` | Serious impact needing a modest precondition: authenticated privilege escalation, stored XSS on a privileged view, IDOR on sensitive records, SSRF to internal services, injection with real reach. |
| `medium` | Real but bounded: reflected XSS needing interaction, CSRF on a meaningful action, missing rate limit with a demonstrated abuse path, weak crypto not yet broken in context. |
| `low` | Minor exposure or hardening gap with a plausible but narrow consequence. |
| `info` | Defense-in-depth / best practice with no realistic security consequence on its own. |

Do not inflate. A missing rate limit is not `critical` without a shown abuse/impact. "Uses JWT", "CORS *", or "no CSP" are not vulnerabilities unless a concrete credential/data-exposure path makes them exploitable. Separate exploitability from defense-in-depth.

## Deduplication

- One **root cause** = one finding, even if it surfaces in several files. List all affected components under it.
- If two domains touch the same issue, the owning domain keeps it; the other references it for cross-domain evidence only.
- Distinct sinks sharing a root cause are one finding; the same class in unrelated code paths are separate.

## Finding record (fields)

Each final finding carries: stable `id` (`SEC-001`…), `title`, `severity`, `confidence`, `category`, `cwe[]` (when identifiable), `components[]`, `evidence[]` (with `file:line`), `preconditions[]`, `impact`, `existing_controls[]`, `remediation[]`, `verification[]` (regression test / method), `gsd_phase`, `change_risk` (low|medium|high), and whether it is independently fixable or has dependencies.

Do not use CVSS precision without enough information to justify it.
