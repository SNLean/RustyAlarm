<!-- refreshed: 2026-08-15 -->
# Architecture

**Analysis Date:** 2026-08-15

## System Overview

RustyAlarm is a Rust raid-alarm notification system with two distinct products sharing only the `rustplus` library:

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                                     │
├──────────────────┬──────────────────┬──────────────────────────────┤
│  Desktop Web UI  │  SaaS Web UI     │  Console Output              │
│  `web/index.html`│  `saas/templates`│  `rust.py` format_logs      │
└────────┬─────────┴────────┬─────────┴──────────┬───────────────────┘
         │                  │                    │
         ▼                  ▼                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                                │
│  Desktop: `webapp.py` (HTTP.Server)  │  SaaS: `saas/app.py` (FastAPI) │
│  `core.py` routing + handlers        │  Request routing + API endpoints│
└──────────┬───────────────────────────┴──────────┬────────────────────┘
           │                                      │
           ▼                                      ▼
┌──────────────────────────────┐    ┌──────────────────────────────────┐
│    MONITOR LAYER             │    │    ASYNC ORCHESTRATION LAYER     │
│  `core.py::AlarmMonitor`     │    │  `saas/monitor.py::Manager`      │
│  - Single alarm per desktop  │    │  - Coordinates N AlarmRunners    │
│  - Runs in thread with lock  │    │  - One coroutine per active alarm│
│  - sync: threading.RLock()   │    │  - Periodic sync() reconciliation│
└──────────┬───────────────────┘    └──────────────┬───────────────────┘
           │                                       │
           ▼                                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  RUST+ PROTOCOL & NOTIFICATIONS                      │
│  `rustplus.RustSocket` (3rd party) ← communication with game server  │
│  `saas/notify.py::send_discord()` ← Discord webhook notifications   │
└──────────────────────────────────────────────────────────────────────┘
           │                                       │
           ▼                                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  PERSISTENCE & CONFIGURATION                         │
│  Desktop: `config.json` (JSON file)  │  SaaS: `saas_data/rustalarm.db` │
│  `core.py` config validation         │  `saas/db.py` SQLite + locking   │
└──────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **Web Handler** (Desktop) | HTTP routing, static files, state snapshots, monitor lifecycle | `webapp.py::Handler` |
| **Web Handler** (SaaS) | HTTP routing, API endpoints, auth, alarm CRUD, webhooks | `saas/app.py` (FastAPI routes) |
| **AlarmMonitor** | Single-alarm polling in dedicated thread, sound playback | `core.py::AlarmMonitor` |
| **AlarmRunner** | Single-alarm async polling coroutine | `saas/monitor.py::AlarmRunner` |
| **Manager** | Multi-alarm orchestration, sync reconciliation | `saas/monitor.py::Manager` |
| **Config** | Environment-based settings for SaaS, JSON file for desktop | `saas/config.py`, `core.py` config functions |
| **Database** | User/session/alarm CRUD with SQLite + global lock | `saas/db.py` |
| **Authentication** | Steam OpenID 2.0 login flow (SaaS only) | `saas/steam.py`, `saas/app.py` auth routes |
| **Notifications** | Discord webhook dispatch | `saas/notify.py::send_discord()` |

## Pattern Overview

**Overall:** Two isolated products (Desktop / SaaS) with dedicated monitor implementations but shared `rustplus` library.

**Key Characteristics:**
- **Desktop**: Single-threaded HTTP server + background async monitor in separate thread (thread-safe via RLock)
- **SaaS**: Multi-user async event loop (FastAPI/uvicorn) + per-alarm coroutines orchestrated by Manager
- **Shared abstraction**: Both implement "configure → validate → connect → poll → notify" lifecycle
- **Validation-first**: Configuration changes are validated before storage (ConfigError, ValidationError)
- **Session isolation**: SaaS isolates users by Steam ID at every database query
- **No multi-process**: Single worker only (explicit in `saas/__main__.py` — multi-worker would duplicate alarms)

## Layers

**Web / Request Handling:**
- Purpose: Accept HTTP requests, route them, serialize responses
- Location: `webapp.py` (desktop), `saas/app.py` (saas)
- Contains: Request handlers, JSON/HTML responses, CSRF/security headers
- Depends on: Config, Monitor/Manager, DB (SaaS only)
- Used by: Browser/client

**Business Logic (Alarm Management):**
- Purpose: Configure alarms, validate input, trigger notifications
- Location: `core.py` (config/validation), `saas/db.py` (CRUD), `saas/app.py` (routes)
- Contains: Validation functions, CRUD operations, alarm state transformation
- Depends on: Config, Database (SaaS), Monitor orchestration
- Used by: Web handlers

**Monitor Orchestration:**
- Purpose: Lifecycle management and state synchronization for alarm pollers
- Location: `saas/monitor.py` (async manager + runners), `core.py` (thread-based monitor)
- Contains: AlarmMonitor class (desktop), Manager/AlarmRunner classes (SaaS)
- Depends on: rustplus library, config
- Used by: Web handlers (to start/stop), Discord notifications

**Rust+ Protocol & Notifications:**
- Purpose: Connect to Rust+ API, poll alarm state, dispatch notifications
- Location: `rustplus` library (external), `saas/notify.py`
- Contains: Socket management, entity polling, webhook calls
- Depends on: httpx (for Discord), rustplus (for Rust+)
- Used by: AlarmMonitor/AlarmRunner

**Persistence:**
- Purpose: Store configuration and audit state
- Location: `config.json` (desktop), `saas_data/rustalarm.db` (SaaS)
- Contains: Alarm config, user/session records, alarm history
- Depends on: OS filesystem (desktop), sqlite3 (SaaS)
- Used by: All layers for reads; web handlers for writes

## Data Flow

### Primary Request Path: Alarm Creation (SaaS)

1. User submits alarm form → `POST /api/alarms` (`saas/app.py:214`)
2. `current_user()` retrieves user from session → `saas/db.py:146`
3. `same_origin()` validates CSRF → `saas/app.py:76`
4. `read_json()` parses request → `saas/app.py:109`
5. `db.create_alarm()` validates + inserts → `saas/db.py:283`
   - `validate_alarm()` checks IP, port, entity_id, intervals → `saas/db.py:198`
   - `is_blocked_host()` blocks private IPs (SSRF protection) → `saas/db.py:182`
6. `await manager.sync()` reconciles DB against active runners → `saas/monitor.py:243`
   - New AlarmRunner spawned, task created → `saas/monitor.py:261`
   - Runner enters `_session()` loop, connects to Rust+ → `saas/monitor.py:101`
7. Response: `{"ok": True, "alarm": {...}}` → client

### Polling Loop: Alarm State Monitoring

**Desktop (threaded):**
1. `webapp.py` POST `/api/monitor/start` → `monitor.start(config)` → `core.py:268`
2. Spawns daemon thread → `core.py:276`
3. Thread runs `asyncio.run(AlarmMonitor._run(config))` → `core.py:300`
4. Connects RustSocket → `core.py:329`
5. Loop: every `CHECK_INTERVAL` seconds → `core.py:345`
   - `await socket.get_entity_info(entity_id)` fetches alarm state
   - On OFF→ON transition (not in cooldown) → `play_sound()` → `core.py:375`
   - Updates `self.alarm_on`, `last_check`, `trigger_count` via lock
6. Web handler reads state via `monitor.snapshot()` (thread-safe lock) → `core.py:248`

**SaaS (async):**
1. `POST /api/alarms` or periodic `Manager.sync()` → `saas/monitor.py:243`
2. For each active alarm in DB: spawn `AlarmRunner.run()` coroutine → `saas/monitor.py:78`
3. Runner establishes RustSocket → `saas/monitor.py:115`
4. Loop: every `check_interval` seconds → `saas/monitor.py:141`
   - `await socket.get_entity_info(entity_id)` fetches alarm state
   - On OFF→ON transition (not in cooldown) → `await _notify()` → `saas/monitor.py:200`
   - `send_discord()` dispatches webhook → `saas/notify.py:11`
   - Updates runner state (no lock needed — single coroutine owns its state)
5. Web handler reads state via `manager.snapshot_for(alarm_ids)` → `saas/monitor.py:265`

**State Management:**
- **Desktop**: Global `monitor` instance in `webapp.py:35`, protected by `threading.RLock()` inside AlarmMonitor
- **SaaS**: Global `manager` instance in `saas/monitor.py:277`, protected by `asyncio.Lock()` for sync operations only
- Both use snapshot pattern: current state frozen at read time (not live bindings)

## Key Abstractions

**AlarmMonitor (Desktop):**
- Purpose: Encapsulates single-alarm polling in a thread-safe container
- Examples: `core.py:198`
- Pattern: Thread spawner + asyncio event loop + RLock for shared state
- Public methods: `start(config)`, `stop()`, `snapshot()`, `logs_since(seq)`

**AlarmRunner (SaaS):**
- Purpose: Encapsulates single-alarm polling as an async coroutine
- Examples: `saas/monitor.py:43`
- Pattern: State holder + async task + deque for log history
- Public methods: `run()` (coroutine entry), `snapshot()`, `log(level, message)`

**Manager (SaaS):**
- Purpose: Orchestrates multiple AlarmRunners, syncs with DB
- Examples: `saas/monitor.py:217`
- Pattern: Dict of runners keyed by alarm_id + periodic reconciliation
- Key method: `sync()` — compare DB against live tasks, add/remove as needed

**ConfigError / ValidationError:**
- Purpose: Carry validation errors from form to client with per-field messages
- Examples: `core.py:77`, `saas/db.py:164`
- Pattern: Exception with `.errors` dict mapping field name → message string

## Entry Points

**Desktop Web Panel:**
- Location: `webapp.py::main()` → `serve()` → `ThreadingHTTPServer` listening on `127.0.0.1:8765`
- Triggers: User runs `python webapp.py` or executes `.spec` build
- Responsibilities: HTTP request handling, config save/load, monitor lifecycle, browser launch

**Desktop Console:**
- Location: `rust.py::main()` → `AlarmMonitor.start()` → polling loop
- Triggers: User runs `python rust.py`
- Responsibilities: Load config, start monitor, print formatted logs to console until interrupted

**SaaS Service:**
- Location: `saas/__main__.py::main()` → `uvicorn.run("saas.app:app")`
- Triggers: `python -m saas` or deployment script
- Responsibilities: FastAPI app lifespan, session/alarm management, multi-user coordination

## Architectural Constraints

- **Threading:** Desktop uses one dedicated thread for monitor (asyncio event loop runs there); SaaS uses uvicorn's event loop (single process, single worker mandated in `saas/__main__.py`)
- **Global state:** 
  - Desktop: `monitor` instance in `webapp.py:35` (module-level global)
  - SaaS: `manager` instance in `saas/monitor.py:277` (module-level global), `_conn` in `saas/db.py:19` (module-level global)
  - Both locked at access points
- **Circular imports:** Minimal risk — `saas/app.py` imports `db`, `steam`, `monitor`, `notify` only; no back-imports
- **Single worker requirement:** SaaS alarm state lives in `manager` (memory). Multiple workers → multiple managers → duplicate monitors per alarm → duplicate Discord notifications. Documented explicitly in `saas/__main__.py:6`
- **Blocking database access:** SaaS uses `asyncio.to_thread(db.active_alarms)` to avoid blocking the event loop while holding the global `_lock` in `db.py`
- **CSRF / Session isolation:** Every DB write checks `user["steam_id"]` (SaaS) or Origin header (desktop webapp). No user can access another's alarms.

## Anti-Patterns

### No Multi-Processing Naive Scaling

**What happens:** Running multiple SaaS workers with uvicorn/gunicorn (e.g., `--workers 4`)
**Why it's wrong:** Each worker has its own `manager` instance. Every enabled alarm spawns in every worker. Result: 4× Discord notifications per trigger, 4× Rust+ API calls, wasted resources, confusion.
**Do this instead:** 
- Use a single uvicorn process as documented → `saas/__main__.py:6`
- If you need horizontal scaling, refactor to use a message queue (Celery/RabbitMQ) to dispatch monitor tasks to workers, or use a leader-election pattern to ensure only one worker runs monitors at a time.

### Validation Not Enforced at Entry

**What happens:** Accepting raw user input into DB without normalization (e.g., storing "28082" as string instead of int in port)
**Why it's wrong:** Type mismatches downstream; unclear intent; hard to parse and validate twice.
**Do this instead:** 
- Always call `validate_alarm()` or equivalent before DB write → `saas/db.py:284`, `core.py:272`
- The validate function returns a clean dict with correct types and ranges → `saas/db.py:264`
- Use that for DB insertion, not the raw payload

### Hardcoded Limits in Magic Numbers

**What happens:** `MIN_INTERVAL = 2` in `saas/monitor.py:24` or check interval min `0.2` in `core.py:134`
**Why it's wrong:** No clear justification; hard to change or reason about without grep-ing the codebase.
**Do this instead:** 
- Document the constant's rationale at definition
- Centralize interval bounds in `config.py` (already done for SaaS: `MAX_ALARMS` → `saas/config.py:31`)
- Desktop desktop could do the same in `core.py` DEFAULTS

## Error Handling

**Strategy:** Fail fast with validation; catch and log transient errors; expose validation errors to client.

**Patterns:**
- **Validation:** `validate_alarm()` returns clean dict or raises `ValidationError(errors)` → handler returns 400 with per-field messages → `saas/app.py:225`, `saas/db.py:262`
- **Transient connection errors:** Retry with exponential backoff (SaaS) or log warning (desktop) → `saas/monitor.py:78`, `core.py:383`
- **Fatal errors:** Set runner status to "error", log, stop polling → `saas/monitor.py:119`, `core.py:304`
- **Secrets in exceptions:** Never log or return webhook URLs in exceptions → `saas/app.py:299`, `saas/monitor.py:213`

## Cross-Cutting Concerns

**Logging:**
- Desktop: `AlarmMonitor.log(level, message)` appends to deque + calls optional callback → `core.py:223`
- SaaS: `AlarmRunner.log(level, message)` appends to deque → `saas/monitor.py:60`, plus `logging` module for infrastructure (FastAPI, rustplus)
- Format: `{"seq": int, "ts": float, "level": str, "message": str}` (identical in both)

**Validation:**
- **Config-level:** `validate_config()` (desktop) → `core.py:97` and `validate_alarm()` (SaaS) → `saas/db.py:198`
- **Field-level:** Numeric ranges, hostname/IP format, Discord URL prefix, SSRF blocking
- **Row-level:** User can only access own alarms (SteamID check)

**Authentication:**
- **SaaS only:** Steam OpenID 2.0 → `saas/steam.py:39`
  - Stateless: session token = random string hashed in DB, no signing
  - CSRF protection: state cookie checked on return → `saas/app.py:167`
- **Desktop:** None (localhost only, configured locally)

---

*Architecture analysis: 2026-08-15*
