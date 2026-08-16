# External Integrations

**Analysis Date:** 2026-08-15

## APIs & External Services

**Rust+ Companion API:**
- Rust+ game server monitoring via the rustplus library
- SDK/Client: `rustplus==6.0.9`
- Protocol: TCP socket connection
- Used in: `core.py` (desktop tool), `saas/monitor.py` (SaaS)
- Server details: `ServerDetails(ip, port, player_id, player_token)`
- Key methods:
  - `RustSocket.connect()` - Returns bool (not exception); `False` if unreachable
  - `socket.get_entity_info(entity_id)` - Returns entity value or `RustError` (check with `isinstance()`)
- Note: Rarely raises; signals failure via return value/`RustError` — see `core.py` error handling

**Steam OpenID 2.0 (SaaS only):**
- Authentication provider (no API key needed)
- Endpoint: `https://steamcommunity.com/openid/login`
- Implementation: `saas/steam.py`
- Flow:
  1. `login_url(state)` → User redirected to Steam
  2. Steam callback to `BASE_URL + /auth/steam/return`
  3. `verify()` → Re-POST params with `mode=check_authentication`
  4. Returns SteamID64 from `claimed_id` field (regex-extracted)
- CSRF protection: `state` parameter bound to cookie, validated on return
- Gotcha: `RUSTALARM_BASE_URL` must match public domain exactly or callback fails
- Used by: `saas/app.py` (`/auth/steam/login`, `/auth/steam/return`)

**Discord Webhooks (SaaS only):**
- Alarm notifications via Discord
- SDK/Client: httpx (custom implementation in `saas/notify.py`)
- Auth: Per-alarm webhook URL stored in DB (`alarms.discord_webhook`)
- Method: `send_discord(webhook_url, alarm_name, server, test=False)`
- Payload: Discord embed (JSON) with:
  - Title: "ALARMA ACTIVADA" (red) or "Prueba de webhook" (green)
  - Description, color, server field, timestamp
  - Error: Raises on non-2xx response
- Used by: `saas/monitor.py` (on alarm trigger); `saas/app.py` (/api/alarms/test endpoint)
- Endpoint: User-provided webhook URL from Discord server settings

## Data Storage

**Databases:**
- SQLite (local file)
  - Provider: stdlib `sqlite3`
  - Type: Relational
  - Location: `saas_data/rustalarm.db` (SaaS only; desktop tool has no database)
  - Client: Direct `sqlite3` connection (not an ORM)
  - Connection: `db.connect()` creates global connection with WAL mode + foreign keys on
  - Synchronization: Global `RLock` around all queries; monitor coroutines call via `asyncio.to_thread()`
  - Schema tables:
    - `users` (steam_id, display_name, plan, plan_active, is_admin, created_at, last_login_at)
    - `sessions` (token, steam_id, created_at, expires_at)
    - `alarms` (id, steam_id, name, ip, port, player_token, entity_id, check_interval, cooldown, discord_webhook, enabled, created_at, updated_at)
  - Indexes: `idx_alarms_steam` (steam_id), `idx_sessions_expiry` (expires_at)
  - See `saas/db.py` lines 21–57 for full schema

**File Storage:**
- Desktop tool:
  - `config.json` - Editable alongside .exe (writable)
  - `alarma.wav` - Audio file (bundled; user can override with own file)
- SaaS:
  - SQLite `.db` + `-wal` + `-shm` files in `saas_data/`
  - No file uploads or blob storage

**Caching:**
- None configured
- SaaS monitor keeps in-memory state:
  - `Manager.runners` - Dict of active `AlarmRunner` tasks
  - `AlarmRunner.logs` - Deque of last 100 log entries per alarm
  - State resets on restart (by design)

## Authentication & Identity

**Auth Provider:**
- Steam (OpenID 2.0, SaaS only)
- Implementation: `saas/steam.py`
- Flow:
  - Login URL: User clicked, browser redirected to `https://steamcommunity.com/openid/login`
  - Return: Steam POSTs to `BASE_URL/auth/steam/return` with signed params
  - Verification: App re-POSTs to Steam with `mode=check_authentication`
  - Result: SteamID64 extracted from `claimed_id` field
- Session: Random token stored in DB, httponly cookie (`rustalarm_session`), 30-day expiry
- Desktop tool: No auth (single-user, local config.json only)

**Secrets Management:**
- Session tokens: Random 256-bit secrets (`secrets.token_urlsafe()`)
- No hardcoded secrets in code
- Environment variables: Read from OS env or .env file
- Discord webhook URLs: Per-alarm, stored in DB (not env var)
- Player token: Stored in config.json (desktop) or DB (SaaS); treated as secret

## Monitoring & Observability

**Error Tracking:**
- None configured (no Sentry, Rollbar, etc.)

**Logs:**
- Desktop tool: Console output + in-memory deque (max 300 entries per AlarmMonitor)
  - Format: `[HH:MM:SS] ICON message`
  - Icons: "i" (info), "OK" (ok), "!" (warn), "X" (error), ">>>" (alarm)
  - Accessed via `monitor.logs_since(seq)` for incremental polling
  - Browser polls `/api/state?since=N` every second
- SaaS monitor: In-memory deque per AlarmRunner (max 100 entries)
  - Format: `{seq, ts, level, message}`
  - Exposed via `/api/alarms/{id}/logs` (browser polls every 2s)
  - Lost on restart
- No persistent logs; stdout only (set to `warning` level in uvicorn config)
- Rust+ logger (`logging.getLogger("rustplus")`) suppressed (set to CRITICAL) to avoid spam

## CI/CD & Deployment

**Hosting:**
- Desktop: Standalone .exe (via PyInstaller)
- SaaS: Self-hosted HTTP/HTTPS (behind reverse proxy like nginx)

**CI Pipeline:**
- None configured

**Build Process:**
- PyInstaller specs:
  - `pyinstaller webapp.spec` → `dist/rust-panel/rust-panel.exe`
  - `pyinstaller rust.spec` → `dist/rust/rust.exe`
- No automated builds; manual invocation

**Deployment (SaaS):**
- `python -m saas` - Starts uvicorn on `RUSTALARM_HOST:RUSTALARM_PORT`
- Systemd/Supervisor recommended for process management
- nginx reverse proxy:
  - Terminates HTTPS
  - Forwards to `127.0.0.1:8000` (localhost only)
  - Sets headers: `X-Forwarded-Proto`, `X-Forwarded-For`
  - FastAPI trusts via `forwarded_allow_ips` config
- Database: SQLite file in `saas_data/` (backup via filesystem snapshots)

## Environment Configuration

**Required env vars (SaaS):**
- `RUSTALARM_BASE_URL` - Public domain URL (critical for Steam login)
- Optional but recommended:
  - `RUSTALARM_HOST` - Listen interface (default `127.0.0.1`)
  - `RUSTALARM_PORT` - Listen port (default `8000`)
  - `RUSTALARM_ADMIN_STEAM_ID` - Admin user SteamID64 (default empty; no admin page access)
  - `RUSTALARM_MAX_ALARMS` - Per-user limit (default 3)
  - `RUSTALARM_DATA_DIR` - SQLite folder (default `./saas_data`)
  - `RUSTALARM_FORWARDED_IPS` - Trusted proxy (default `127.0.0.1`)

**Desktop tool (config.json):**
- JSON structure with fields: IP, PORT, STEAM_ID, PLAYER_TOKEN, ALARM_ENTITY_ID, CHECK_INTERVAL, COOLDOWN
- Created/edited via `webapp.py` panel
- Location: Next to executable when frozen

**Secrets location:**
- .env file (gitignored, not checked in)
- Environment variables at runtime
- config.json (desktop; gitignored)
- saas_data/ folder (gitignored; SQLite + session tokens)

## Webhooks & Callbacks

**Incoming (SaaS):**
- Steam OpenID 2.0 callback: `POST /auth/steam/return`
  - Triggered by user clicking "Login with Steam"
  - Params: OpenID response (signed by Steam)
  - Returns: Redirect to panel or error

**Outgoing (SaaS):**
- Discord webhook: `POST {webhook_url}` (user-provided)
  - Triggered: Alarm fires (if webhook configured) + test button
  - Payload: Discord embed (JSON)
  - No retry logic; raises on error

**Internal (Desktop):**
- `webapp.py` → `localhost:8765/api/*` - Local panel polling
  - `GET /api/state?since=N` - Config + monitor state + new logs
  - `POST /api/config` - Save config
  - `POST /api/monitor/start` - Start monitoring
  - `POST /api/monitor/stop` - Stop monitoring
  - `POST /api/sound/test` - Play alarm sound
  - `POST /api/sound/stop` - Stop playing

**Internal (SaaS):**
- Frontend → `FastAPI` routes
  - `GET /` - Landing page
  - `GET /auth/steam/login` - Begin Steam login
  - `GET /auth/steam/return` - Steam callback
  - `GET /panel` - User alarm panel
  - `GET /admin` - Admin page (owner only)
  - `GET /api/alarms` - List user's alarms (JSON)
  - `POST/PUT/DELETE /api/alarms/{id}` - CRUD alarms
  - `POST /api/alarms/{id}/test` - Test Discord webhook
  - `POST /api/logout` - End session

## Cross-Domain & CORS

**Desktop:**
- Single local host (`127.0.0.1:8765`); no cross-domain requests
- Host header check (`_host_ok`) prevents DNS rebinding attacks
- All requests from localhost

**SaaS:**
- Steam OpenID: `form_action 'self' https://steamcommunity.com` (CSP allows submit to Steam only)
- Discord webhooks: Outbound only (no CORS); direct HTTP POST
- Frontend: Same-origin only (no CORS headers set)
- CSRF: Origin/Referer check on all mutating routes (`same_origin()`)

---

*Integration audit: 2026-08-15*
