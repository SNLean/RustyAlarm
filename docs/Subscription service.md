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
| `saas/app.py` | FastAPI routes, header middleware, session, alarms API, admin, `/static` mount |
| `saas/db.py` | SQLite (sync + `RLock`), alarm validation, SSRF host guard |
| `saas/monitor.py` | `Manager` + `AlarmRunner`: one coroutine per alarm |
| `saas/pairing.py` | Native Rust+ pairing (FCM/Expo register + MCS listener); driven by the `extension/` |
| `saas/verify.py` | One-shot live check of an alarm before it is created (resolve + connect + entity type) |
| `saas/sounds.py` | Alarm-sound catalog (built-in + admin uploads); path-traversal-safe `resolve()` |
| `saas/steam.py` | [[Steam OpenID]] login (no API key) |
| `saas/notify.py` | Alert to [[Discord Webhooks]] |
| `saas/config.py` | Config via `RUSTALARM_*` environment variables |
| `saas/templates/` | Jinja2: landing, panel, admin (Spanish — end-user facing). Icons: self-hosted Font Awesome under `saas/static/fa/` |

## User flow

1. Landing (`/`) → **Sign in with Steam** button → [[Steam OpenID]].
2. Panel (`/panel`): alarm CRUD, live status (polls `/api/alarms` every 2 s), "Test Discord" button, per-alarm sound. New alarms use a **guided step-by-step wizard** (onboarding + in-app guides); see [[Log/2026-08-15 — Guided alarm wizard]].
3. Admin (`/admin`, owner only): pause/activate accounts, and manage the **sound catalog** (upload/delete). See [[Product decisions]] for why account gating is manual.

### Pairing, verification and sound (the wizard)

- **Pairing is the only way in.** The four connection fields (ip/port/player_token/entity_id) can't be typed — they come from a real Rust+ pairing, enforced server-side (`create_alarm` reads them from the user's live pairing session, never from the client). The browser **extension** (`extension/`) captures the Facepunch token and delivers it to `/api/pair/link`; the wizard auto-fills and auto-advances as the server/alarm pairings arrive. Full story: [[Rust+ pairing]].
- **Live verification.** On the summary step the wizard calls `/api/pair/verify` (`saas/verify.py`): one ephemeral connection confirms the credentials work and the entity is a Smart Alarm (`AppEntityType.Alarm == 2`) — a soft gate that catches the wipe-`not_found` trap up front.
- **Custom sound.** Each alarm picks a catalog sound; the panel plays it when `trigger_count` increases and the page is open (frontend-only, the monitor is untouched). See [[Product decisions]].

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

SQLite at `saas_data/rustalarm.db`, WAL mode, one global `RLock`. Coroutines touch it via `asyncio.to_thread`. Three tables: `users`, `sessions`, `alarms` (the `alarms.sound` column arrived via an `ALTER TABLE` migration in `db.connect()`). It is gitignored — **treat it as production; never run DB-writing tests against it** (see [[Pitfalls and fixes]]).

## Security

Invariants in [[Security review]]: `same_origin()` (CSRF) on every mutating route, queries scoped by `steam_id` (tenant isolation), anti-CSRF `state` on login, escaping in the panel, CSP + `X-Frame-Options` headers. Newer surfaces keep the line: the connection fields are pairing-only (no client-supplied credentials), `/api/pair/link` is authorised by a single-use nonce (not a cookie), `verify.py` resolves+pins to stop SSRF, and sound uploads are admin-only with a size cap and a traversal-safe `resolve()`. Bugs found and fixed along the way: [[Pitfalls and fixes]].

> [!warning] rustplus + uvicorn event-loop trap
> `saas/app.py` lifespan pins the event loop with `asyncio.set_event_loop(asyncio.get_running_loop())`. Without it, [[rustplus]] schedules its response handlers on a non-running loop and every `get_entity_info` returns "No response received". Do not remove that line — full detail in [[rustplus]] and [[Pitfalls and fixes]].
