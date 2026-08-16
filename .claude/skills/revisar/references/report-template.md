# Report template

Exact output format for the artifacts written under `.planning/security-audit/<dir>/`. Keep IDs stable across artifacts.

## `SECURITY-REVIEW.md`

```markdown
# Security Review — <repo/scope>

## Executive summary
- Scope reviewed / excluded
- Count by severity: critical N · high N · medium N · low N · info N
- Top 3–5 risks (one line each)
- Any CRITICAL/HIGH left NOT_VERIFIED

## Attack surface
Highest-risk entry points, trust boundaries, and files (from the surface map).

## Findings
For each finding:
### SEC-001 — <title>
- Severity / Confidence / Category / CWE
- Components: file:line …
- Evidence: concrete trace source → sink
- Preconditions / attacker & trust boundary
- Impact
- Existing controls / framework protections
- Remediation
- Verification (regression test / method)
- GSD phase · Change risk · Independent or dependent

## Not verified
Material areas that could not be checked and what is needed to verify them.

## Tools run / unavailable
```

## `FINDINGS.json`

```json
{
  "audit_scope": "",
  "summary": { "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0 },
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

## `GSD-REMEDIATION.md`

Ordered phases with: goal, findings covered, dependencies/order, acceptance criteria, required tests, rollout notes, and the proposed GSD commands per phase (see [[remediation-gsd]]).

## `VERIFY-CHECKLIST.md`

One checkable line per finding: how to prove the fix (the test to run / the manual check), referencing `SEC-xxx`.

## `AUDIT-METADATA.md`

Date · repository/scope · git branch/commit (if available) · arguments · tools actually run · tools unavailable (`TOOL_NOT_AVAILABLE`) · exclusions · agents used · GSD detected/not detected · important assumptions.

## Final response (chat)

Scope · count by severity · top 3–5 risks · any CRITICAL/HIGH still NOT_VERIFIED · report directory · recommended first GSD phase · exact next command. If nothing confirmed, do not say "secure" — say no confirmed vulnerabilities were found in the reviewed scope and list what was not verified.
