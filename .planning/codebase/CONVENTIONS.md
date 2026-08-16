# Coding Conventions

**Analysis Date:** 2026-08-15

## Naming Patterns

**Files:**
- `snake_case.py` - All Python files use lowercase with underscores
- Examples: `core.py`, `webapp.py`, `app.py`, `db.py`, `monitor.py`, `notify.py`, `steam.py`

**Functions:**
- `snake_case()` - All functions use lowercase with underscores
- Examples: `base_dir()`, `load_config()`, `validate_config()`, `play_sound()`, `send_discord()`
- Private/internal functions prefixed with underscore: `_hash_token()`, `_session()`, `_notify()`, `_run()`, `_host_ok()`, `_csrf_ok()`, `_state()`

**Variables:**
- `snake_case` - Lowercase with underscores
- Module-level state variables: `_lock`, `_conn`, `_thread`, `_loop`, `_logs`, `_seq`, `_start_lock`
- Constants for sentinel values: `status`, `detail`, `alarm_on` (instance attributes)

**Types:**
- `PascalCase` - All classes use PascalCase
- Examples: `AlarmMonitor`, `ConfigError`, `ValidationError`, `Handler`, `AlarmRunner`, `Manager`

**Constants:**
- `UPPER_CASE` - All module-level constants use uppercase with underscores
- Examples: `DEFAULTS`, `CONFIG_PATH`, `ICONS`, `SECURE_COOKIES`, `BIG_INT_FIELDS`, `OAUTH_STATE_COOKIE`, `EMBED_COLOR_ALARM`, `EMBED_COLOR_TEST`, `SYNC_INTERVAL`, `RETRY_BASE`, `RETRY_MAX`

## Code Style

**Formatting:**
- No automated code formatter configured (no `.prettierrc`, `pyproject.toml`, or similar)
- String quotes: Double quotes preferred throughout
- Indentation: 4 spaces (Python standard)
- Line continuations: Implicit (parentheses, square brackets, curly braces)

**Linting:**
- No configured linter (no `.eslintrc`, `pyproject.toml` with flake8/pylint config)
- Style is enforced through convention and code review, not automation
- Minimal type hints used (see Type Hints section below)

**Documentation Language:**
- **All code comments and docstrings are written in Spanish by design**
- This includes module docstrings, function docstrings, and inline comments
- See `core.py` line 1-5 for example: `"""Nucleo compartido: rutas, configuracion y monitor de alarma Rust+."""`
- English used only in internal documentation vault (separate from codebase)

## Import Organization

**Order:**
1. Standard library imports (e.g., `import asyncio`, `from pathlib import Path`)
2. Third-party imports (e.g., `from fastapi import FastAPI`, `import httpx`, `from rustplus import RustSocket`)
3. Local/relative imports (e.g., `from . import db`, `from .config import BASE_URL`)

**Examples from `saas/app.py`:**
```python
# Standard library
import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

# Third-party
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Local
from . import db, steam
from .config import ADMIN_STEAM_ID, BASE_URL, MAX_ALARMS, SESSION_COOKIE, SESSION_DAYS
from .monitor import manager
from .notify import send_discord
```

**Path Aliases:**
- Relative imports use dot notation: `from . import module`, `from .config import CONSTANT`
- Avoid `sys.path` manipulation; rely on package structure

## Error Handling

**Custom Exceptions:**
- Define exception classes near the top of modules: `ConfigError` in `core.py` (line 77), `ValidationError` in `saas/db.py` (line 164)
- Store validation errors in `errors` dict attribute: `exc.errors` contains field-level error messages
- Exception messages are in Spanish

**Validation Pattern:**
- Collect all errors into a dict, then raise once at the end (not early exit per error)
- Example from `core.py:validate_config()` (line 97-150) and `saas/db.py:validate_alarm()` (line 198-264):
  ```python
  errors = {}
  clean = dict(DEFAULTS)
  
  # Multiple validation checks
  ip = str(data.get("IP", "")).strip()
  if not ip:
      errors["IP"] = "Requerido"
  clean["IP"] = ip
  
  # ... more validations ...
  
  if errors:
      raise ConfigError(errors)
  return clean
  ```

**Exception Handling:**
- Broad exception handlers for expected failures: `except ConfigError as exc:`, `except ValidationError as exc:`
- Log the error and return it to client: See `webapp.py:151-156` and `saas/app.py:214-228`
- Never expose internal errors to clients — catch, log (if sensitive), and return generic message

**Async Exception Handling:**
- Respect `asyncio.CancelledError`: re-raise it immediately (see `saas/monitor.py:83-84`, `115-116`, `147-148`)
- Wrap broad exception handlers outside try-except for CancelledError

## Logging

**Framework:** Standard `logging` module + custom `log()` methods in classes

**Application-Level Logging:**
- Classes with internal logging: `AlarmMonitor` (`core.py`), `AlarmRunner` (`saas/monitor.py`), `Handler` (`webapp.py`)
- Custom `log(level, message)` method stores entries in deque + calls optional callback
- Log entry structure:
  ```python
  {
      "seq": int,           # monotonic sequence number
      "ts": float,          # time.time() timestamp
      "level": str,         # one of: "info", "ok", "warn", "error", "alarm"
      "message": str,       # log message
  }
  ```

**Log Levels Used:**
- `"info"` - Informational: normal operation progress
- `"ok"` - Success: operation completed successfully
- `"warn"` - Warning: degraded operation or recoverable failure
- `"error"` - Error: operation failed, may retry
- `"alarm"` - Alert: alarm triggered (special level for high-priority events)

**CLI Output:**
- Use `print()` for end-user output in CLI tools (`rust.py`, `webapp.py`)
- Example mapping in `rust.py:11-17`:
  ```python
  ICONS = {
      "info": "i",
      "ok": "OK",
      "warn": "!",
      "error": "X",
      "alarm": ">>>",
  }
  ```

**Third-Party Logging:**
- Suppress noisy loggers explicitly: `logging.getLogger("rustplus").setLevel(logging.CRITICAL)` in `core.py:25`
- Rust+ logger needs active cleanup: `quiet_rustplus_logger()` in `saas/monitor.py:28-40` (called after each socket creation to prevent handler accumulation)

## Comments

**Inline Comments:**
- Explain WHY, not WHAT (WHAT should be obvious from code)
- Security-focused comments: CSRF protection, SSRF protection, token security
- Examples:
  - `core.py:153-155`: Explains why `BIG_INT_FIELDS` must travel as strings (JavaScript `Number.MAX_SAFE_INTEGER` overflow)
  - `core.py:170-171`: Explains atomic write strategy for config (unique per-process temp file prevents concurrent clobber)
  - `saas/db.py:129-130`: Explains why session tokens are hashed (DB dump shouldn't grant sessions)

**Docstrings:**
- All functions, classes, and modules have docstrings in Spanish
- Single-line docstrings for simple functions: `"""Carpeta de datos editables (config.json, alarma.wav)."""`
- Multi-line docstrings for complex logic, including explanation of what it returns/raises
- Example from `core.py:30-37`:
  ```python
  def base_dir() -> Path:
      """Carpeta de datos editables (config.json, alarma.wav).

      Congelado con PyInstaller apunta a la carpeta del .exe, no a _MEIPASS,
      porque config.json tiene que poder escribirse y sobrevivir al cierre.
      """
  ```

## Function Design

**Size:**
- Small focused functions (10-50 lines typical)
- Some larger methods when they represent a single operation: `_run()` method in `AlarmRunner` can be 50+ lines for single retry loop

**Parameters:**
- Positional args for required data: `log(level, message)`
- Keyword-only args for options: `send_discord(webhook_url, *, alarm_name, server, test=False)` in `saas/notify.py:11`
- Default values near function definition, not scattered

**Return Values:**
- Single return type per function (no Union of disparate types)
- Return `None` for void operations (or implicit `None`)
- Return dicts for structured data: `config_for_client()`, `snapshot()`, `validate_alarm()`
- Return native types for simple values: strings, ints, bools

**Type Hints:**
- Minimal use of type hints (Python 3.14 project but hints are sparse)
- When used: simple types only (str, bool, dict, None)
- Example from `saas/steam.py:39`: `async def verify(query_params) -> str | None:`
- Function arguments typically untyped; return type specified if non-obvious

## Module Design

**Exports:**
- Functions and classes used directly by other modules are defined at module level (not wrapped in `__all__`)
- Example: `core.py` exports `AlarmMonitor`, `ConfigError`, `load_config()`, `validate_config()`, etc. (imported in `webapp.py:18-29`)

**Module Constants:**
- Configuration loaded at import time from environment or defaults
- Example: `saas/config.py` defines `BASE_URL`, `HOST`, `PORT`, `DB_PATH` as module-level constants
- These are used throughout; no global singleton pattern (simple module globals are fine)

**Global State:**
- Module-level locks for thread-safe access: `_lock = threading.RLock()` in `saas/db.py:18`
- Module-level connections/instances: `_conn = None` in `saas/db.py:19`, `manager = Manager()` in `saas/monitor.py:277`
- All state access guarded by locks: See `saas/db.py:_run()` (line 73-84)

**Barrel Files:**
- `__init__.py` documents module purpose; examples:
  - `saas/__init__.py` (3 lines): Describes the SaaS service and startup command
  - Does not re-export symbols; clients import from specific submodules

## Special Patterns

**Atomic File Operations:**
- Config saves use temp file + rename: `saas/db.py` line 171-175 (per-process temp file prevents concurrent writes)

**Thread Safety:**
- Use `threading.RLock()` for reentrant locking (classes may call themselves)
- All database access goes through `_run()` which acquires lock: `saas/db.py:73-84`
- Async-safe bridge: `asyncio.to_thread()` for blocking DB calls: `saas/monitor.py:246`

**Async/Await:**
- Async functions used in FastAPI (`saas/app.py`) and `saas/monitor.py`
- Sync wrapper for database: `await asyncio.to_thread(db.active_alarms)` in `saas/monitor.py:246`
- Always respect `asyncio.CancelledError`: catch other exceptions, re-raise this one

**Security-Focused Code:**
- Input validation is strict and always normalizes before use
- File paths validated: no path traversal, hostnames sanitized for SSRF
- Example: `saas/db.py:198-217` validates IP/hostname, blocking private/loopback ranges
- Comments explain security rationale: See comments about number encoding, CSRF, SSRF

---

*Convention analysis: 2026-08-15*
