---
title: Subscription service
tags:
  - saas
  - rustyalarm
---

# Subscription service (`saas/`)

Multi-user web app. One [[FastAPI and Uvicorn|uvicorn]] process, one event loop; the web routes and every alarm monitor share it.

## Modules

| File | Role |
|---|---|
| `saas/app.py` | FastAPI routes, header middleware, session, alarms API, admin |
| `saas/db.py` | SQLite (sync + `RLock`), alarm validation |
| `saas/monitor.py` | `Manager` + `AlarmRunner`: one coroutine per alarm |
| `saas/steam.py` | [[Steam OpenID]] login (no API key) |
| `saas/notify.py` | Alert to [[Discord Webhooks]] |
| `saas/config.py` | Config via `RUSTALARM_*` environment variables |
| `saas/templates/` | Jinja2: landing, panel, admin (Spanish — end-user facing) |

## User flow

1. Landing (`/`) → **Sign in with Steam** button → [[Steam OpenID]].
2. Panel (`/panel`): alarm CRUD, live status (polls `/api/alarms` every 2 s), "Test Discord" button. New alarms use a **guided step-by-step wizard** (onboarding + in-app guides); see [[Log/2026-08-15 — Guided alarm wizard]].
3. Admin (`/admin`, owner only): pause/activate accounts. See [[Product decisions]] for why it is manual.

## The monitor

`Manager` reconciles the `alarms` table against the live coroutines: compares `updated_at`, cancels stale ones, starts missing ones. Runs after every CRUD and every 30 s.

`AlarmRunner`:
- Exponential backoff on connection failure (15 s → 300 s).
- Counts consecutive failed responses (`RECONNECT_AFTER`) to detect a dead socket, because [[rustplus]] does not raise when the socket drops.
- Cooldown to avoid repeating the Discord alert.
- Live state (status, logs) is **in memory only**: restarting loses it, by design.

> [!note] `active_alarms()` filters by plan
> The query joins `alarms` with `users.plan_active`. Pausing a user stops their alarms with no extra code. See [[Product decisions]].

## Database

SQLite at `saas_data/rustalarm.db`, WAL mode, one global `RLock`. Coroutines touch it via `asyncio.to_thread`. Three tables: `users`, `sessions`, `alarms`. It is gitignored.

## Security

Invariants in [[Security review]]: `same_origin()` (CSRF) on every mutating route, queries scoped by `steam_id` (tenant isolation), anti-CSRF `state` on login, escaping in the panel, CSP + `X-Frame-Options` headers.
