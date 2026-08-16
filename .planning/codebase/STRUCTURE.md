# Codebase Structure

**Analysis Date:** 2026-08-15

## Directory Layout

```
C:/Users/PC/Desktop/RUST APP/
├── saas/                          # SaaS multi-user FastAPI service
│   ├── __init__.py
│   ├── __main__.py                # Entry point: uvicorn runner
│   ├── app.py                     # FastAPI routes: auth, alarm CRUD, admin
│   ├── config.py                  # Environment configuration (BASE_URL, PORT, MAX_ALARMS)
│   ├── db.py                      # SQLite: users, sessions, alarms + validation
│   ├── monitor.py                 # Async orchestration: Manager + AlarmRunner
│   ├── notify.py                  # Discord webhook dispatch
│   ├── steam.py                   # Steam OpenID 2.0 login
│   └── templates/                 # Jinja2 HTML templates
│       ├── base.html              # Base layout
│       ├── landing.html           # Login page
│       ├── panel.html             # User alarm dashboard
│       └── admin.html             # Admin user management
├── core.py                        # Shared desktop: config, validation, AlarmMonitor class
├── webapp.py                      # Desktop: HTTP.Server + panel at localhost:8765
├── rust.py                        # Desktop: console mode (no UI)
├── web/                           # Desktop web UI assets
│   └── index.html                 # Single-page dashboard (config form, monitor logs)
├── config.json                    # Desktop: alarm config (created by webapp, read by rust.py)
├── config.example.json            # Desktop: config template
├── alarma.wav                     # Desktop: sound alert file
├── requirements.txt               # Python dependencies (FastAPI, uvicorn, rustplus, etc.)
├── saas_data/                     # SaaS data directory (auto-created, excluded from git)
│   └── rustalarm.db               # SQLite database
├── .env.example                   # Environment variable template for SaaS
├── .gitignore                     # Excludes config.json, saas_data/, etc.
├── deploy/                        # Production deployment scripts
│   └── DEPLOY.md                  # VPS + nginx setup guide
├── docs/                          # Obsidian vault documentation (excluded from analysis)
├── .planning/                     # Planning and analysis (excluded from analysis)
│   └── codebase/                  # Generated architecture/structure docs
├── CLAUDE.md                      # Agent guidelines for code modifications
└── README.md                      # Project overview
```

## Directory Purposes

**`saas/`:**
- Purpose: Multi-user SaaS product — hosted web application with user accounts, alarm management, Discord notifications
- Contains: FastAPI application, SQLite database schema, async alarm orchestration, authentication, email/webhook templates
- Key files: `app.py` (routing), `db.py` (persistence + validation), `monitor.py` (alarm polling orchestration), `config.py` (environment settings)

**`saas/templates/`:**
- Purpose: Jinja2 HTML templates rendered server-side for the SaaS web UI
- Contains: Login page, user dashboard, admin panel
- Key files: `landing.html` (sign-in with Steam), `panel.html` (alarm CRUD interface), `admin.html` (user management for admins)

**Root (desktop tools):**
- Purpose: Single-user desktop application — configuration, console CLI, web panel
- Contains: Config validation, alarm monitor class, HTTP server for local web UI
- Key files: `core.py` (config + AlarmMonitor), `webapp.py` (local web panel), `rust.py` (console mode)

**`web/`:**
- Purpose: Frontend assets for desktop web panel (localhost:8765)
- Contains: Single HTML file with embedded CSS/JavaScript for configuration, logging, monitor control
- Key files: `index.html` (complete UI)

**`deploy/`:**
- Purpose: Production deployment documentation and scripts
- Contains: DEPLOY.md with VPS setup (Ubuntu, nginx, systemd, HTTPS/SSL)

**`docs/`:**
- Purpose: Obsidian vault with architecture decisions, security, deployment, and references (excluded from this analysis)

## Key File Locations

**Entry Points:**
- `saas/__main__.py`: SaaS service launcher (`python -m saas`)
- `webapp.py`: Desktop web panel launcher (`python webapp.py`)
- `rust.py`: Desktop console mode launcher (`python rust.py`)

**Configuration:**
- `saas/config.py`: Environment-based SaaS configuration (BASE_URL, PORT, MAX_ALARMS, ADMIN_STEAM_ID)
- `config.json`: File-based desktop configuration (IP, port, Steam ID, intervals) — created by webapp, read by rust.py
- `config.example.json`: Desktop config template
- `.env.example`: SaaS environment variable template

**Core Logic:**
- `saas/app.py`: FastAPI routes (auth, CRUD, admin, webhooks)
- `saas/db.py`: SQLite operations + validation (users, sessions, alarms, plan management)
- `saas/monitor.py`: Async alarm runner orchestration (Manager class, AlarmRunner class)
- `saas/notify.py`: Discord webhook client
- `saas/steam.py`: Steam OpenID authentication
- `core.py`: Desktop config validation, AlarmMonitor class (threading + asyncio)
- `webapp.py`: Desktop HTTP server and request handlers

**Testing:**
- No dedicated test directory — tests managed externally (see `CLAUDE.md`)

**Assets:**
- `web/index.html`: Desktop panel UI (HTML + embedded CSS/JavaScript)
- `alarma.wav`: Sound file for alarm alerts
- `saas/templates/*.html`: Server-rendered templates for SaaS web UI

## Naming Conventions

**Files:**
- Lowercase snake_case: `app.py`, `config.py`, `monitor.py`, `notify.py`, `steam.py`, `db.py`
- Exception: `webapp.py`, `rust.py` (desktop entry points, pre-existing convention)
- HTML templates: lowercase with `.html`: `panel.html`, `admin.html`

**Directories:**
- Lowercase snake_case: `saas/`, `templates/`, `deploy/`, `docs/`, `web/`
- Convention: module packages use lowercase (Python 3 convention)

**Functions:**
- Lowercase snake_case: `login_url()`, `validate_config()`, `upsert_user()`, `get_entity_info()`
- Private functions: prefix underscore: `_run()`, `_session()`, `_notify()`, `_thread_main()`

**Variables:**
- Constants: UPPERCASE: `MAX_ALARMS`, `MIN_INTERVAL`, `DEFAULTS`, `SESSION_DAYS`, `SECURE_COOKIES`
- Module-level globals: lowercase prefixed underscore: `_conn`, `_lock`, `_logs`, `_loop`, `_thread`
- Instance attributes: lowercase: `self.status`, `self.detail`, `self.alarm_on`, `self.rows`

**Types/Classes:**
- PascalCase: `AlarmMonitor`, `AlarmRunner`, `Manager`, `Handler`, `ConfigError`, `ValidationError`, `ServerDetails`, `RustSocket`

## Where to Add New Code

**New Feature in SaaS (e.g., alarm mute timer):**
- Primary code: `saas/db.py` (add schema column + CRUD function), `saas/app.py` (add POST/PUT endpoint)
- Validation: `saas/db.py::validate_alarm()` (add field checks)
- Notification logic: `saas/monitor.py::AlarmRunner._notify()` (check mute status before sending)
- Template: `saas/templates/panel.html` (add form field + JavaScript handler)

**New Feature in Desktop (e.g., alarm repeat counter):**
- Primary code: `core.py::AlarmMonitor` (add attribute + update in polling loop)
- Config: `core.py::DEFAULTS` (add default value), `core.py::validate_config()` (add validation)
- UI: `web/index.html` (add display + form field)
- Persistence: `config.json` schema + save logic in `webapp.py` or `core.py`

**New External Integration (e.g., Slack notifications):**
- **SaaS:** 
  - Add: `saas/slack.py` (webhook dispatch function, similar to `saas/notify.py`)
  - Modify: `saas/db.py::validate_alarm()` (validate Slack webhook URL)
  - Modify: `saas/monitor.py::AlarmRunner._notify()` (call Slack sender)
  - Modify: `saas/app.py` (add test-webhook endpoint like line 279)
  - Template: `saas/templates/panel.html` (add Slack URL form field)
- **Desktop:** Not applicable (single-user, no webhooks)

**New Utility Function:**
- Shared validation: Add to `core.py` if used by both products, or `saas/db.py` if SaaS-only
- Database operation (SaaS): Add to `saas/db.py` following pattern of `_run(sql, params, fetch=...)`
- Monitoring state (both): Keep in respective Monitor classes, access via `snapshot()`

**New Route/Endpoint (SaaS):**
- Add to `saas/app.py` with `@app.get()`, `@app.post()`, etc.
- Include security checks: `current_user()`, `same_origin()` (CSRF), `is_admin()` if needed
- Import supporting functions from `saas/db.py`, `saas/notify.py`, etc.
- Set appropriate Content-Type and status codes (see patterns in existing endpoints, ~200-404)

## Special Directories

**`saas_data/`:**
- Purpose: Runtime data storage for SaaS (SQLite database)
- Generated: Yes (auto-created by `saas/config.py:22` if missing)
- Committed: No (in `.gitignore` — contains user data, never commit)
- Permissions: Must be writable by the uvicorn process

**`web/`:**
- Purpose: Desktop web UI assets
- Generated: No (hand-written HTML/CSS/JavaScript)
- Committed: Yes (part of source)
- Bundled: Yes (included in PyInstaller `.spec` builds)

**`saas/templates/`:**
- Purpose: Server-side Jinja2 templates for SaaS
- Generated: No (hand-written)
- Committed: Yes (part of source)
- Bundled: Yes (deployed with SaaS code)

**`deploy/`:**
- Purpose: Production deployment documentation
- Generated: No (hand-written)
- Committed: Yes (part of source)
- Bundled: No (for reference; deployment runs from deployed server)

## File Dependencies & Import Graph

```
saas/app.py (main entry point)
  ├── imports: db, steam, monitor, notify, config
  └── used by: uvicorn (saas/__main__.py)

saas/monitor.py
  ├── imports: db (for active_alarms), notify (for send_discord)
  └── used by: app.py (creates manager singleton)

saas/db.py
  ├── imports: config (for DB_PATH, MAX_ALARMS, SESSION_DAYS)
  └── used by: app.py, monitor.py

saas/notify.py
  ├── imports: httpx (3rd party)
  └── used by: monitor.py (AlarmRunner._notify), app.py (test-webhook endpoint)

saas/steam.py
  ├── imports: httpx (3rd party), config (for BASE_URL)
  └── used by: app.py (login/auth routes)

webapp.py (desktop entry point)
  ├── imports: core (AlarmMonitor, config functions)
  └── standalone; not imported elsewhere

rust.py (desktop console entry point)
  ├── imports: core (AlarmMonitor, config functions)
  └── standalone; not imported elsewhere

core.py (shared desktop)
  ├── imports: rustplus (3rd party RustSocket)
  └── used by: webapp.py, rust.py
```

## Configuration & Environment

**SaaS (environment variables, read from `saas/config.py`):**
- `RUSTALARM_BASE_URL`: Public URL for Steam OAuth callback (default: `http://127.0.0.1:8000`)
- `RUSTALARM_HOST`: Listen address (default: `127.0.0.1`)
- `RUSTALARM_PORT`: Listen port (default: `8000`)
- `RUSTALARM_ADMIN_STEAM_ID`: SteamID64 for admin access (optional)
- `RUSTALARM_MAX_ALARMS`: Alarms per user limit (default: `3`)
- `RUSTALARM_DATA_DIR`: SQLite data directory (default: `./saas_data`)
- `RUSTALARM_FORWARDED_IPS`: Trusted proxy IPs for X-Forwarded-* headers (default: `127.0.0.1`)

**Desktop (JSON file, read from `core.py`):**
- `config.json` keys: `IP`, `PORT`, `STEAM_ID`, `PLAYER_TOKEN`, `ALARM_ENTITY_ID`, `CHECK_INTERVAL`, `COOLDOWN`
- Location: `core.py::CONFIG_PATH` (same directory as executable or `core.py`)
- Accessed by: `webapp.py` (form save/load), `rust.py` (load on startup)

## Project Structure Summary

| Aspect | Desktop | SaaS |
|--------|---------|------|
| **Entry point** | `webapp.py`, `rust.py` | `saas/__main__.py` |
| **Server** | stdlib `http.server.ThreadingHTTPServer` | FastAPI + uvicorn |
| **Database** | `config.json` (file) | SQLite (saas_data/rustalarm.db) |
| **Authentication** | None (localhost only) | Steam OpenID 2.0 |
| **Monitoring** | Single AlarmMonitor in thread | Multiple AlarmRunner coroutines |
| **Concurrency** | Threading + asyncio | Pure asyncio (event loop based) |
| **Notifications** | Windows `winsound` only | Discord webhooks |
| **Config** | File-based `config.json` | Environment variables |

---

*Structure analysis: 2026-08-15*
