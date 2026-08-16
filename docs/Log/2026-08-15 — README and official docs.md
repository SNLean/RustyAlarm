---
title: 2026-08-15 — README and official docs
tags:
  - log
  - session
  - docs
date: 2026-08-15
---

# 2026-08-15 — README and official docs

The repo `README.md` was written (previously a 2-line stub). It is the project's official documentation: the repo's front door.

## What the README covers

- What RustyAlarm is and the two products ([[Architecture]]).
- Getting started: service (`python -m saas`) and desktop (`python webapp.py`).
- How to get the Rust+ data (link to [[Rust+ pairing]]).
- Documentation index: points to this vault (`docs/`, [[Home]]), to `deploy/DEPLOY.md` ([[VPS deployment]]) and to `CLAUDE.md`.
- Stack, security ([[Security review]]) and a note on gitignored secrets.

## Documentation state

- **README.md** — repo front door. ✓
- **Vault `docs/`** — complete internal documentation: thematic notes + `References/` (official docs per dependency) + `Log/` (per-session journal). Now in English. ✓
- **deploy/DEPLOY.md** — production. ✓
- **CLAUDE.md** — guide for agents. ✓

## Vault language migration

Later in the session the whole vault was translated to **English** (for better tooling/recall), while everything the end user sees stays in **Spanish**. Folders renamed `Referencias/`→`References/`, `Registro/`→`Log/`. Rule recorded in [[Maintaining this vault]].
