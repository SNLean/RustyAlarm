# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Two products in one repo, both watching Rust (the game) Smart Alarms through the Rust+ companion API. UI strings and code comments are in Spanish; keep that. No test suite, no linter config, no package manifest, no git repository.

1. **Local desktop tool** (`core.py`, `webapp.py`, `rust.py`, `web/`): single-user, plays `alarma.wav` through `winsound` on this PC. Console runner + local config panel.
2. **Subscription service** (`saas/`): multi-user hosted product. Steam OpenID login, per-user alarm configs in SQLite, one asyncio coroutine per alarm, alerts via Discord webhook. Payments not integrated yet — `users.plan_active` is toggled manually from `/admin` (env `RUSTALARM_ADMIN_STEAM_ID` marks the owner).

The two share nothing but the `rustplus` library; changes to one must not touch the other.

## Commands

```bash
python -m saas
```

Subscription service — serves `http://127.0.0.1:8000/` (uvicorn). Config via env vars, all prefixed `RUSTALARM_` (see `saas/config.py`): `BASE_URL` (must match the public URL or Steam login breaks), `HOST`, `PORT`, `ADMIN_STEAM_ID`, `MAX_ALARMS`. Data lands in `saas_data/` (SQLite DB + auto-generated session secret) — never commit or publish that folder.

```bash
python webapp.py
```

Local desktop panel — serves `http://127.0.0.1:8765/` and opens a browser. Flags: `--port N`, `--no-browser`.

```bash
python rust.py
```

Console mode — reads `config.json`, connects, polls until Ctrl+C. Refuses to start (with per-field messages) if the config is invalid.

```bash
pyinstaller webapp.spec
```

```bash
pyinstaller rust.spec
```

Builds `dist/rust-panel/rust-panel.exe` and `dist/rust/rust.exe` respectively. `build/` and `dist/` are generated output; do not hand-edit them.

## Runtime environment

- Python 3.14, packages installed globally (no virtualenv in this project). `pip` is not on PATH — use `python -m pip`.
- The desktop tool is Windows-only by construction: `winsound` drives playback (imported defensively in `core.py`, but there is no fallback). The SaaS has no sound and runs anywhere Python does.
- `rustplus` 6.0.9 (pulls in `betterproto`, `numpy`). The `RustSocket(ServerDetails(ip, port, player_id, player_token))` shape is the 6.x API and differs from older releases — pin to 6.x when reinstalling. The desktop panel is stdlib-only; the SaaS adds `fastapi`, `uvicorn`, `jinja2`, `httpx`, `python-multipart`.

## Architecture — subscription service (`saas/`)

Single uvicorn process, single event loop; the web routes and every alarm monitor share it.

- **`db.py`** — sqlite3 (sync) guarded by one global `RLock`, WAL mode. Monitor coroutines call it through `asyncio.to_thread`. `validate_alarm` collects all field errors into `ValidationError.errors` (field → Spanish message) for inline form rendering. `active_alarms()` joins against `users.plan_active` — pausing a user pauses their alarms with no extra code.
- **`steam.py`** — Steam OpenID 2.0, no API key needed. Verification re-POSTs the callback params with `mode=check_authentication`; the SteamID64 comes from `claimed_id` (regex-anchored). `BASE_URL` mismatch here is the classic "login always fails" cause.
- **`monitor.py`** — `Manager` reconciles the `alarms` table against running `AlarmRunner` coroutines: compares `updated_at`, cancels stale, starts missing. Called after every CRUD and every 30s. Runner: exponential backoff on connect failure (15s→300s), 5 consecutive poll errors = assume dead socket and reconnect, cooldown suppresses repeat Discord alerts. Live state (status, logs ring buffer) is in-memory only — restart loses it, by design.
- **`app.py`** — session cookie (random token in DB, httponly, SameSite=Lax) + Origin/Referer check on every mutating route (CSRF). Every alarm query is scoped by the session's `steam_id` — keep it that way; that is the entire multi-tenant isolation story. `alarm_to_client` stringifies big ints (steam_id/player_token/entity_id exceed JS `MAX_SAFE_INTEGER`).
- **Templates** (`saas/templates/`) — Jinja2, dark rust theme, `base.html` holds shared CSS/JS helpers (`api`, `send`, `toast`). Panel polls `/api/alarms` every 2s.

## Architecture — local desktop tool

**`core.py`** — everything stateful, imports without side effects.

- *Paths.* `base_dir()` is the writable data folder (the `.exe` folder when frozen, **not** `_MEIPASS`); `bundle_dir()` is read-only packaged assets (`_MEIPASS` when frozen). `CONFIG_PATH` lives in `base_dir()` so it survives and stays editable. `sound_path()` prefers an `alarma.wav` next to the exe and falls back to the bundled copy, which is how a user swaps the sound without rebuilding.
- *Config.* `load_config` merges onto `DEFAULTS` and never throws on a missing file. `validate_config` normalises and collects **all** field errors into `ConfigError.errors` (field → Spanish message) rather than failing on the first one — the web panel renders that map inline under the inputs. `save_config` validates then writes atomically via a `.tmp` + `replace`.
- *`AlarmMonitor`.* Owns a daemon thread running its own `asyncio` loop. Public state is read under an `RLock` through `snapshot()`; `stop()` signals across threads with `loop.call_soon_threadsafe(event.set)` and joins. The poll loop waits with `asyncio.wait_for(stop_event.wait(), timeout=interval)` so a stop is immediate instead of sleeping out the interval. Logs go to a bounded `deque` with a monotonic `seq`, and `logs_since(seq)` is what makes the browser's incremental polling cheap.

**`webapp.py`** — `ThreadingHTTPServer` bound to `127.0.0.1` only, plus a `Host`-header check (`_host_ok`) against DNS rebinding. Holds the single module-level `monitor`. Endpoints: `GET /api/state?since=N` (config + monitor snapshot + new log lines), `POST /api/config`, `POST /api/monitor/start` (saves the posted form, then starts — so what runs is always what is on disk), `POST /api/monitor/stop`, `POST /api/sound/test`, `POST /api/sound/stop`. Validation failures return 400 with `{error, errors}`.

**`web/index.html`** — single self-contained page, no build step, no dependencies. Polls `/api/state` every second carrying the last seen `seq`. Inputs are locked while the monitor runs; a `dirty` flag stops the poller from overwriting text the user is typing.

**`rust.py`** — thin console entrypoint over the same `AlarmMonitor`, using its `on_log` callback to print.

## Things that will bite you

- **rustplus 6.0.9 rarely raises; it signals failure by return value.** `socket.get_entity_info()` returns a `RustError` (with `.reason`) on a bad/wiped entity — `isinstance(entity, RustError)` before touching `.value`. And `socket.connect()` returns `False` (never raises) when the server is unreachable — you must check the bool. A silently dead socket keeps returning `RustError`/`None` without an exception, so the SaaS monitor counts consecutive failed responses (`RECONNECT_AFTER`) to decide the socket died, rather than waiting for a raise that never comes. Both traps were live bugs caught in review.
- **rustplus adds a fresh DEBUG log handler to logger `rustplus.py` on every `RustSocket()` construction.** Constructing one per reconnect leaks handlers unbounded (memory + duplicated log spam). `monitor.quiet_rustplus_logger()` clears them after each construction; the desktop `core.py` avoids it by building one socket per run. Note the logger name is `rustplus.py`, not `rustplus`.
- **`socket.get_entity_info()` returns errors, it does not raise them** — see above; the desktop `config.json` entity ID answers `not_found` against that server, so a live run logs warnings rather than alarms until the ID is repaired.
- **Big integers must stay strings across the JS boundary** — `STEAM_ID` (~7.6e16) exceeds JS `Number.MAX_SAFE_INTEGER` (9.0e15). Desktop: `config_for_client()` / `validate_config`. SaaS: `alarm_to_client()` stringifies `steam_id`/`player_token`/`entity_id`; `db.validate_alarm` parses back. Keep the HTML inputs `type="text"`; sending raw JSON numbers corrupts them on round-trip.
- **In the SaaS panel, escape every value before building HTML.** `cardHtml` assembles markup as strings and assigns via `innerHTML` — any unescaped field (name, ip, detail, log message) is stored XSS. Use the `esc()` helper on all of them, and never serialize an alarm object (it carries `player_token`/`discord_webhook`) into an HTML attribute — edit-by-id reads from the in-memory `alarmsById` map instead. Both were review findings.
- **SaaS security invariants, do not weaken:** every mutating route calls `same_origin()` (CSRF) and scopes DB queries by the session's `steam_id` (tenant isolation); Steam login binds a `state` cookie against the signed `return_to` (login-CSRF); a middleware sets CSP + `X-Frame-Options: DENY`. `db.validate_alarm` rejects non-ASCII digits in `port` (`"٤"` passes `str.isdigit()`), non-finite floats, and non-hostname characters in `ip`.
- **`config.json` is deliberately never bundled.** `_MEIPASS` is a read-only temp dir wiped on exit, so a bundled config could not be edited. Frozen builds create and edit it next to the `.exe`.
- **Console output needs `flush=True`** when frozen or piped, otherwise the log appears only at exit.
- **`pip` in the project root is a stray 0-byte file**, not a script or lockfile. Safe to delete.
- **`config.json` holds live server credentials** (`STEAM_ID`, `PLAYER_TOKEN`). Do not copy its contents into logs, issues, or anything published.

## `.history/`

Timestamped snapshots from the VS Code Local History extension (`rust_<YYYYMMDDHHMMSS>.py`, `config_<...>.json`). It is the only version history that exists here — useful for recovering an earlier form of the script — but it is not source and should not be edited or imported.
