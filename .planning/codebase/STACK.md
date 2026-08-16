# Technology Stack

**Analysis Date:** 2026-08-15

## Languages

**Primary:**
- Python 3.14 - Entire codebase (desktop tool + SaaS service)

## Runtime

**Environment:**
- Windows (desktop tool via `winsound` is Windows-only; SaaS runs on any Python platform)

**Package Manager:**
- pip (packages installed globally, no virtualenv in project)
- Lockfile: Not used (direct pip install from `requirements.txt`)

## Frameworks

**Core (Desktop Tool):**
- `http.server` (Python stdlib) - `ThreadingHTTPServer` in `webapp.py`, bound to `127.0.0.1:8765`
- `asyncio` (Python stdlib) - Event loop in `AlarmMonitor` running in daemon thread
- `winsound` (Python stdlib, Windows-only) - Audio playback via `alarma.wav`

**Web (SaaS Service):**
- FastAPI 0.141.1 - HTTP framework with async support, Uvicorn ASGI server
- Uvicorn[standard] 0.52.3 - ASGI server (single-process, single-worker only)
- Jinja2 3.1.6 - Template rendering for landing, login, panel, admin pages (`saas/templates/`)

**Frontend:**
- Vanilla JavaScript (no build step, no dependencies)
- Single self-contained HTML page (`web/index.html` for desktop, `saas/templates/panel.html` for SaaS)

**Testing:**
- None configured (no test framework, no linter, no test suite mentioned in CLAUDE.md)

**Build/Packaging:**
- PyInstaller - Builds standalone executables:
  - `pyinstaller webapp.spec` → `dist/rust-panel/rust-panel.exe`
  - `pyinstaller rust.spec` → `dist/rust/rust.exe`

## Key Dependencies

**Critical:**
- rustplus 6.0.9 - Rust+ companion API client library
  - Pulls in: `betterproto`, `numpy`
  - Note: Pinned to 6.x for API compatibility; older/newer versions have different `RustSocket` shape
  - Quirk: Never raises exceptions; signals failure via return values (`False`, `RustError`) — see CLAUDE.md line 76

**Core (Desktop + SaaS):**
- httpx 0.28.1 - Async HTTP client (used in `saas/steam.py`, `saas/notify.py` for webhooks)

**SaaS-specific:**
- fastapi 0.141.1 - Web framework
- uvicorn[standard] 0.52.3 - ASGI server
- jinja2 3.1.6 - Template engine
- python-multipart 0.0.32 - Form parsing for FastAPI

**Infrastructure:**
- sqlite3 (Python stdlib) - Database for SaaS (WAL mode, global `RLock` synchronization)

## Configuration

**Environment (Desktop Tool):**
- Reads `config.json` (JSON key-value):
  - `IP`, `PORT` - Rust server details
  - `STEAM_ID`, `PLAYER_TOKEN`, `ALARM_ENTITY_ID` - Credentials (large integers stored as strings to avoid JS rounding)
  - `CHECK_INTERVAL` (seconds), `COOLDOWN` (seconds) - Timing
  - Defaults in `DEFAULTS` dict (`core.py` line 66)
- Location: `base_dir() / "config.json"` (next to .exe when frozen)
- Created/edited by `webapp.py` panel; validated atomically via temp file + rename

**Environment (SaaS Service):**
- Reads via env vars, all prefixed `RUSTALARM_`:
  - `RUSTALARM_BASE_URL` - Public URL (must match for Steam login callback)
  - `RUSTALARM_HOST`, `RUSTALARM_PORT` - Bind address (default `127.0.0.1:8000`)
  - `RUSTALARM_ADMIN_STEAM_ID` - SteamID64 of service owner (sees `/admin` page)
  - `RUSTALARM_MAX_ALARMS` - Alarms per user (default 3)
  - `RUSTALARM_DATA_DIR` - SQLite + secrets folder (default `./saas_data`)
  - `RUSTALARM_FORWARDED_IPS` - Trusted proxy IPs for `X-Forwarded-*` headers (default `127.0.0.1`)
- See `saas/config.py` for defaults

**Build:**
- PyInstaller specs: `webapp.spec`, `rust.spec`
  - Desktop webapp bundles `web/index.html` + `alarma.wav`
  - Console tool bundles `alarma.wav` only (config.json deliberately not bundled; must be editable)

## Data Storage

**Desktop Tool:**
- `config.json` - Configuration (JSON, writable next to .exe)
- `alarma.wav` - Audio file (bundled; user can override with their own next to .exe)

**SaaS Service:**
- SQLite database: `saas_data/rustalarm.db`
  - Tables: `users`, `sessions`, `alarms`
  - WAL mode for concurrency; global `RLock` around all access
  - Monitor coroutines call DB via `asyncio.to_thread()` to avoid blocking event loop
  - See `saas/db.py` for schema

## Platform Requirements

**Development:**
- Python 3.14
- rustplus 6.0.9 (strictly 6.x)
- pip (no venv in project)

**Desktop Tool Production:**
- Windows only (winsound import, no fallback)
- Standalone .exe from PyInstaller build

**SaaS Production:**
- Python 3.14 runtime
- Single uvicorn process (no multiprocessing; monitor state is in-memory)
- Network: listens on configured `HOST:PORT`, expects reverse proxy for HTTPS
- nginx recommended (sets `X-Forwarded-Proto`, `X-Forwarded-For`; FastAPI trusts via `forwarded_allow_ips`)
- SQLite requires filesystem with WAL support

## Security Considerations

**Environment:**
- `.env` file present (`.env.example` provided; `.env` not checked in)
- No secrets in source code; env vars only

**Hardening Notes (from CLAUDE.md):**
- Desktop: Host-header check against DNS rebinding (`_host_ok` in `webapp.py`)
- SaaS: CSP, X-Frame-Options: DENY, CSRF (Origin/Referer check on mutating routes), SameSite cookies
- Session tokens: random (not signed); stored in DB with expiry
- Big integers: Steam IDs exceed JS `MAX_SAFE_INTEGER`, travel as strings; validated back on server

## Known Deployment Notes

- **Single process only.** Multi-worker/gunicorn setup breaks monitor (state not shared; duplicate Discord alerts).
- **WAL mode SQLite.** Filesystem must support `*-wal` + `*-shm` files.
- **`X-Forwarded-*` headers.** Behind a reverse proxy; FastAPI configured to trust `forwarded_allow_ips`.
- **Steam login.** `RUSTALARM_BASE_URL` must match public domain exactly or Steam callback fails.

---

*Stack analysis: 2026-08-15*
