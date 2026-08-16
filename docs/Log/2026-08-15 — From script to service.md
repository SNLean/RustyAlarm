---
title: 2026-08-15 — From script to service
tags:
  - log
  - session
date: 2026-08-15
---

# 2026-08-15 — From script to service

Log of the session where RustyAlarm went from a loose script to a hosted service with a repo and deploy. Durable context distilled into the thematic notes ([[Home]]).

## What was done

1. Initial repo `CLAUDE.md` (guide for agents).
2. **Desktop refactor**: `core.py` with no import side effects; `webapp.py` (local panel) + `rust.py` (console) over one `AlarmMonitor`. See [[Desktop tool]]. Old bugs fixed along the way: `last_state` never updated (sounded on every poll), `COOLDOWN` never applied, CWD-relative paths.
3. **Pairing guides** in the panel, aligned with the official docs. See [[Rust+ pairing]].
4. **Subscription service** (`saas/`): [[Steam OpenID]] login, per-user alarms in SQLite, asyncio monitor, [[Discord Webhooks]] alert, admin. See [[Subscription service]] and [[Architecture]].
5. **Adversarial review** (31 agents): 19 findings, 16 fixed and verified live. See [[Security review]].
6. **Git**: private repo [SNLean/RustyAlarm](https://github.com/SNLean/RustyAlarm), `.gitignore` excluding secrets, `requirements.txt`, `.env.example`, `config.example.json`. A credential mismatch was resolved (git was `BriYlean`, the repo is `SNLean`).
7. **Deploy** for Ubuntu VPS + nginx: `deploy/rustyalarm.service`, `deploy/nginx.conf`, `deploy/DEPLOY.md`. See [[VPS deployment]].
8. **This Obsidian vault** under `docs/`.

## Decisions taken

Detail in [[Product decisions]]: no payments yet (manual plan), Discord alerts, Steam login, VPS hosting.

## Pending

- Run the `deploy/DEPLOY.md` steps on the real VPS.
- Integrate a payment provider (drives `plan_active`).
- Optional: `deploy/backup.sh` via cron, one-line update script.

## Sources consulted this session

- [rustplus (repo)](https://github.com/olijeffers0n/rustplus) · [docs](https://rplus.ollieee.xyz)
- [rplus — Getting Player Details](https://rplus.ollieee.xyz/getting-started/getting-player-details.md)
- [liamcottle/rustplus.js](https://github.com/liamcottle/rustplus.js)
- [FastAPI](https://fastapi.tiangolo.com/) · [Uvicorn deployment](https://www.uvicorn.org/deployment/)
- [Certbot](https://certbot.eff.org/instructions)
