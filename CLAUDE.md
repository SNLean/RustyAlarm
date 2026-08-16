# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

RustyAlarm: two products in one repo, both watching Rust (the game) Smart Alarms through the Rust+ companion API. Everything the end user sees (templates, wizard, errors, README) and code comments are in Spanish; internal documentation (`docs/` vault, `.planning/`) is in English — keep both conventions. No test suite or linter yet; adding tests + CI is Phase 1 of the current roadmap (`.planning/ROADMAP.md`).

1. **Local desktop tool** (`core.py`, `webapp.py`, `rust.py`, `web/`): single-user, plays `alarma.wav` through `winsound` on this PC. Console runner + local config panel.
2. **Subscription service** (`saas/`): multi-user hosted product — this is the product. Steam OpenID login, per-user alarm configs in SQLite, one asyncio coroutine per alarm, alerts via Discord webhook. Payments not integrated yet — `users.plan_active` is toggled manually from `/admin` (env `RUSTALARM_ADMIN_STEAM_ID` marks the owner); reversing that is planned this milestone (PAY-01).

The two share nothing but the `rustplus` library; changes to one must not touch the other.

## Commands

```bash
python -m pip install -r requirements.txt
```

SaaS dependencies, pinned. The desktop tool needs only `rustplus` beyond the stdlib. `pip` is not on PATH — always `python -m pip`.

```bash
python -m saas
```

Subscription service — serves `http://127.0.0.1:8000/` (uvicorn). Config via env vars, all prefixed `RUSTALARM_` (see `saas/config.py` and `.env.example`): `BASE_URL` (must match the public URL or Steam login breaks; non-https warns at startup), `HOST`, `PORT`, `ADMIN_STEAM_ID`, `MAX_ALARMS`, `DATA_DIR`. Data lands in `saas_data/` (SQLite DB; session tokens stored hashed) — never commit or publish that folder.

**Run exactly one worker.** Monitor state is in-memory (one coroutine per alarm); multiple workers would each open every alarm and duplicate Discord alerts. No gunicorn multi-process, no `--workers`.

```bash
python webapp.py
```

Local desktop panel — serves `http://127.0.0.1:8765/` and opens a browser. Flags: `--port N`, `--no-browser`.

```bash
python rust.py
```

Console mode — reads `config.json` (template: `config.example.json`), connects, polls until Ctrl+C. Refuses to start (with per-field messages) if the config is invalid.

```bash
pyinstaller webapp.spec
```

```bash
pyinstaller rust.spec
```

Builds `dist/rust-panel/rust-panel.exe` and `dist/rust/rust.exe` respectively. `build/` and `dist/` are generated output; do not hand-edit them.

## Runtime environment

- Python 3.14, packages installed globally (no virtualenv in this project).
- The desktop tool is Windows-only by construction: `winsound` drives playback (imported defensively in `core.py`, but there is no fallback). The SaaS has no sound and runs anywhere Python does; production target is an Ubuntu VPS behind nginx (`deploy/`).
- `rustplus` 6.0.9 (pulls in `betterproto`, `numpy`). The `RustSocket(ServerDetails(ip, port, player_id, player_token))` shape is the 6.x API and differs from older releases — pin to 6.x when reinstalling. The desktop panel is stdlib-only; the SaaS adds `fastapi`, `uvicorn`, `jinja2`, `httpx`, `python-multipart` (versions in `requirements.txt`).

## Repo map beyond the code

- **`README.md`** — Spanish, user-facing.
- **`docs/`** — Obsidian vault, in English; the project's real documentation: architecture, product decisions, security review, VPS deployment, per-dependency references (`docs/References/`), and a per-session log (`docs/Log/`). Keep it updated when meaningful work lands — conventions in `docs/Maintaining this vault.md`, index in `docs/Home.md`.
- **`deploy/`** — production deploy: `DEPLOY.md` walkthrough (Ubuntu + nginx + HTTPS), `nginx.conf` (TLS, `server_tokens off`, rate limits on login/API), `rustyalarm.service` (systemd, single worker).
- **`.planning/`** — GSD planning state (PROJECT/REQUIREMENTS/ROADMAP/STATE, `codebase/` maps, `security-audit/` reports). Managed through the `/gsd:*` commands; read `.planning/STATE.md` for the current phase before planning work.
- **`.claude/skills/revisar`** + **`.claude/agents/security-*`** — repo-local `/revisar` security-audit skill and its reviewer agents.
- **`skills/`** — vendored design/animation skill library (reference material, not product code).
- **`.history/`** — VS Code Local History snapshots predating git. Git is now the authoritative history; `.history/` is only useful for pre-git archaeology. Not source; never edit or import it.

## Architecture — subscription service (`saas/`)

Single uvicorn process, single event loop; the web routes and every alarm monitor share it.

- **`db.py`** — sqlite3 (sync) guarded by one global `RLock`, WAL mode. Monitor coroutines call it through `asyncio.to_thread`. Session tokens are sha256-hashed at rest — the raw token lives only in the cookie. `validate_alarm` collects all field errors into `ValidationError.errors` (field → Spanish message) for inline form rendering, and calls `is_blocked_host()` to reject private/loopback/link-local/metadata IPs (SSRF guard). `active_alarms()` joins against `users.plan_active` — pausing a user pauses their alarms with no extra code.
- **`steam.py`** — Steam OpenID 2.0, no API key needed. Verification re-POSTs the callback params with `mode=check_authentication`; the SteamID64 comes from `claimed_id` (regex-anchored, exact `is_valid` line match). `BASE_URL` mismatch here is the classic "login always fails" cause.
- **`monitor.py`** — `Manager` reconciles the `alarms` table against running `AlarmRunner` coroutines: compares `updated_at`, cancels stale, starts missing. Called after every CRUD and every 30s. Runner: exponential backoff on connect failure (15s→300s), 5 consecutive poll errors = assume dead socket and reconnect, cooldown suppresses repeat Discord alerts. Live state (status, logs ring buffer) is in-memory only — restart loses it, by design.
- **`notify.py`** — Discord webhook embeds via httpx (alarm + webhook-test variants); raises if Discord rejects. Callers must not echo the exception to the client or logs — it can contain the webhook URL.
- **`verify.py`** — one-shot live verification before an alarm is created: opens a single ephemeral `RustSocket` to the paired ip:port, calls `get_entity_info`, and confirms the entity is a Smart Alarm (`AppEntityType.Alarm == 2`; Switch=1/StorageMonitor=3 rejected). Never raises — returns `{ok, entity_type, value}` or `{ok:false, code, message}` (error taxonomy, Spanish messages). Wraps `connect()`/`get_entity_info` in `asyncio.wait_for` (both can hang), checks `connect()`'s bool and `isinstance(RustError)` before `.type`/`.value`, always `disconnect()`s in `finally`, and calls `quiet_rustplus_logger()` after construction. The route `POST /api/pair/verify` gates it with `same_origin`, `db.validate_connection` (shares `is_blocked_host` SSRF + range rules with `validate_alarm` via `_validate_connection_fields`), and an in-memory per-user rate limit (`_verify_inflight`/`_verify_last`) — each verify is an on-demand outbound connect, so throttling stops it being a port scanner. The wizard auto-runs it on the summary step as a **soft gate** (a failed check still lets the user create — the server may be transiently down — but says why).
- **`pairing.py`** — native Rust+ pairing for the wizard: registers FCM credentials (`push_receiver.AndroidFCM`, a transitive dep of `rustplus`), gets an Expo push token, sends the user to the Facepunch companion login (`returnUrl` → `/pair/callback?token=…`), registers the device, then listens on MCS (`mtalk.google.com:5228`, fallback `443`) in a stoppable daemon thread. Pairing notifications (`app_data["body"]` JSON, `type` server/entity) fill the wizard via `GET /api/pair/status` polling. All state in memory; the Facepunch AuthToken is used once and discarded — never store or log it. It drives `PushReceiver`'s name-mangled privates and injects `__open` (the stock one blocks forever and can't stop) — pinned via `rustPlusPushReceiver==0.6.1`; re-check if that dep ever moves. **The automatic flow needs a public HTTPS `BASE_URL`** (see the "bite you" note); `/api/pair/start` refuses on non-https and the wizard falls back to the manual-paste box.
- **`app.py`** — session cookie (random token, hashed in DB, httponly, SameSite=Lax) + Origin/Referer check on every mutating route (CSRF). Every alarm query is scoped by the session's `steam_id` — keep it that way; that is the entire multi-tenant isolation story. `alarm_to_client` stringifies big ints (steam_id/player_token/entity_id exceed JS `MAX_SAFE_INTEGER`).
- **Templates** (`saas/templates/`) — Jinja2, dark rust theme. `base.html` holds the design-token system (layered warm-dark surfaces, rust + signal-green, radii/shadow/motion tokens) and shared JS helpers (`api`, `send`, `toast`, scroll-reveal); no external fonts or assets — the CSP blocks them. `panel.html` contains the guided step-by-step alarm-creation wizard and polls `/api/alarms` every 2s. `admin.html` escapes every interpolation.

## Architecture — local desktop tool

**`core.py`** — everything stateful, imports without side effects.

- *Paths.* `base_dir()` is the writable data folder (the `.exe` folder when frozen, **not** `_MEIPASS`); `bundle_dir()` is read-only packaged assets (`_MEIPASS` when frozen). `CONFIG_PATH` lives in `base_dir()` so it survives and stays editable. `sound_path()` prefers an `alarma.wav` next to the exe and falls back to the bundled copy, which is how a user swaps the sound without rebuilding.
- *Config.* `load_config` merges onto `DEFAULTS` and never throws on a missing file. `validate_config` normalises and collects **all** field errors into `ConfigError.errors` (field → Spanish message) rather than failing on the first one — the web panel renders that map inline under the inputs. `save_config` validates then writes atomically via a per-pid `.tmp` + `replace`.
- *`AlarmMonitor`.* Owns a daemon thread running its own `asyncio` loop. Public state is read under an `RLock` through `snapshot()`; `stop()` signals across threads with `loop.call_soon_threadsafe(event.set)` and joins. The poll loop waits with `asyncio.wait_for(stop_event.wait(), timeout=interval)` so a stop is immediate instead of sleeping out the interval. Logs go to a bounded `deque` with a monotonic `seq`, and `logs_since(seq)` is what makes the browser's incremental polling cheap.

**`webapp.py`** — `ThreadingHTTPServer` bound to `127.0.0.1` only, plus a `Host`-header check (`_host_ok`) against DNS rebinding. CSRF hardening: mutating requests must send `Content-Type: application/json` (forces a CORS preflight that is never answered) and the `Origin` header is validated when present; responses carry `X-Frame-Options`/`nosniff`/CSP. Holds the single module-level `monitor`. Endpoints: `GET /api/state?since=N` (config + monitor snapshot + new log lines), `POST /api/config`, `POST /api/monitor/start` (saves the posted form, then starts — so what runs is always what is on disk), `POST /api/monitor/stop`, `POST /api/sound/test`, `POST /api/sound/stop`. Validation failures return 400 with `{error, errors}`.

**`web/index.html`** — single self-contained page, no build step, no dependencies. Polls `/api/state` every second carrying the last seen `seq`. Inputs are locked while the monitor runs; a `dirty` flag stops the poller from overwriting text the user is typing.

**`rust.py`** — thin console entrypoint over the same `AlarmMonitor`, using its `on_log` callback to print.

## Things that will bite you

- **rustplus 6.0.9 rarely raises; it signals failure by return value.** `socket.get_entity_info()` returns a `RustError` (with `.reason`) on a bad/wiped entity — `isinstance(entity, RustError)` before touching `.value`. And `socket.connect()` returns `False` (never raises) when the server is unreachable — you must check the bool. A silently dead socket keeps returning `RustError`/`None` without an exception, so the SaaS monitor counts consecutive failed responses (`RECONNECT_AFTER`) to decide the socket died, rather than waiting for a raise that never comes. Both traps were live bugs caught in review.
- **rustplus adds a fresh DEBUG log handler to logger `rustplus.py` on every `RustSocket()` construction.** Constructing one per reconnect leaks handlers unbounded (memory + duplicated log spam). `monitor.quiet_rustplus_logger()` clears them after each construction; the desktop `core.py` avoids it by building one socket per run. Note the logger name is `rustplus.py`, not `rustplus`.
- **`socket.get_entity_info()` returns errors, it does not raise them** — see above; the desktop `config.json` entity ID answers `not_found` against that server, so a live run logs warnings rather than alarms until the ID is repaired.
- **Big integers must stay strings across the JS boundary** — `STEAM_ID` (~7.6e16) exceeds JS `Number.MAX_SAFE_INTEGER` (9.0e15). Desktop: `config_for_client()` / `validate_config`. SaaS: `alarm_to_client()` stringifies `steam_id`/`player_token`/`entity_id`; `db.validate_alarm` parses back. Keep the HTML inputs `type="text"`; sending raw JSON numbers corrupts them on round-trip.
- **In the SaaS panel, escape every value before building HTML.** `cardHtml` assembles markup as strings and assigns via `innerHTML` — any unescaped field (name, ip, detail, log message) is stored XSS. Use the `esc()` helper on all of them, and never serialize an alarm object (it carries `player_token`/`discord_webhook`) into an HTML attribute — edit-by-id reads from the in-memory `alarmsById` map instead. Both were review findings.
- **SaaS security invariants, do not weaken:** every mutating route calls `same_origin()` (CSRF) and scopes DB queries by the session's `steam_id` (tenant isolation); Steam login binds a random `state` cookie against the `state` echoed through the OpenID-signed `return_to` (login-CSRF); session tokens are hashed at rest; a middleware sets CSP + `X-Frame-Options: DENY`. `db.validate_alarm` rejects non-ASCII digits in `port` (`"٤"` passes `str.isdigit()`), non-finite floats, non-hostname characters in `ip`, and blocked (internal) hosts. The full audit trail lives in `.planning/security-audit/2026-08-15/` and `docs/Security review.md`.
- **Rust+ companion pairing hands the token back via `ReactNativeWebView.postMessage`, NOT a plain redirect.** After Steam login, Facepunch's page calls `window.ReactNativeWebView.postMessage(tokenJson)` — the mobile app / a browser with `--disable-web-security` (rustplus.js CLI) catches it by injecting the shim into the cross-origin popup. A hosted web app cannot inject there. What DOES work for a hosted site is Facepunch's `?token=` **top-level redirect to a public HTTPS `returnUrl`** (this is how the community ollieee site and our `/pair/callback` receive it). Consequence: automatic pairing only works when `BASE_URL` is public HTTPS; on `http://127.0.0.1` Facepunch never delivers the token and the flow hangs at "waiting_login". Local dev and any fallback use the wizard's **manual-paste** box (paste the pairing JSON — ip/port/playerToken or entityId).
- **`is_blocked_host` does NOT resolve DNS** — a public hostname whose A record points at an internal IP passes it. The live-verify path (`verify.py._safe_resolve`) closes this: it resolves the host, rejects if any resolved address is blocked, and connects to the **pinned** IP (no rebind between check and connect). It also blocks packed-numeric IP notations (`2130706433`, `0x…`, octal `0177.0.0.1`) that `ipaddress` won't parse but glibc `getaddrinfo` expands to loopback. The **monitor path (`create_alarm` → `AlarmRunner`) still resolves at connect time and keeps the DNS-rebind hole** — deferred hardening; if you touch it, resolve+pin+recheck there too.
- **Discord webhook URLs are secrets.** Never include the httpx exception text for a webhook post in a client response or log line — it can carry the full webhook URL.
- **`config.json` is deliberately never bundled.** `_MEIPASS` is a read-only temp dir wiped on exit, so a bundled config could not be edited. Frozen builds create and edit it next to the `.exe`.
- **Console output needs `flush=True`** when frozen or piped, otherwise the log appears only at exit.
- **`config.json` holds live server credentials** (`STEAM_ID`, `PLAYER_TOKEN`), and `saas_data/` holds user data — both gitignored; never copy their contents into logs, issues, or anything published.
- **`pip` in the project root is a stray 0-byte file** (gitignored), not a script or lockfile. Safe to delete.
