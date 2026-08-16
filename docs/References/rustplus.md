---
title: rustplus
tags:
  - reference
  - dependency
aliases:
  - rustplus.py
  - RustSocket
---

# rustplus (Python library)

Rust+ API wrapper used by **both** products ([[Architecture]]). Pinned version: **6.0.9** (in `requirements.txt`).

- Repo: [github.com/olijeffers0n/rustplus](https://github.com/olijeffers0n/rustplus)
- Docs: [rplus.ollieee.xyz](https://rplus.ollieee.xyz)
- PyPI: [pypi.org/project/rustplus](https://pypi.org/project/rustplus/)

## Base API

```python
from rustplus import RustSocket, ServerDetails
socket = RustSocket(ServerDetails(ip, port, player_id, player_token))
await socket.connect()
entity = await socket.get_entity_info(entity_id)
```

This shape is 6.x and differs from older versions. Pin to 6.x when reinstalling.

- [Docs — RustSocket](https://rplus.ollieee.xyz/getting-started/rustsocket.md)
- [Docs — Getting Entity Information](https://rplus.ollieee.xyz/api-methods/getting-entity-information.md)

## Gotchas (all verified against 6.0.9)

> [!bug] Signals failure by return value, not by exception
> - `socket.connect()` returns `False` (does not raise) when the server does not respond. **You must check the bool.**
> - `socket.get_entity_info()` returns a `RustError` (with `.reason`) for a bad/wiped entity. `isinstance(entity, RustError)` before touching `.value`.
> - A dead socket keeps returning `RustError`/`None` without raising. The monitor counts consecutive failed responses (`RECONNECT_AFTER`) to decide to reconnect. See [[Subscription service]].

> [!bug] Logging handler leak
> It adds a new DEBUG `StreamHandler` to the `rustplus.py` logger on **every** `RustSocket()` construction. Building one per reconnect accumulates them without bound (memory + duplicated logs). `monitor.quiet_rustplus_logger()` clears them. Note the logger is named `rustplus.py`, not `rustplus`.

> [!bug] Schedules its read-handlers on the wrong event loop under uvicorn
> `ws.run_coroutine_non_blocking` does `asyncio.get_event_loop_policy().get_event_loop().create_task(...)` for both `run_proto_event` and — critically — `handle_message` (which matches responses to requests). Under [[FastAPI and Uvicorn|uvicorn]] that can resolve to a **non-running** loop, so `handle_message` never runs → every `send_and_get` times out after `RESPONSE_TIMEOUT` (5 s) → `get_entity_info()` returns `RustError("No response received")` and the alarm shows "error" forever, even though `connect()` succeeded. **Fix:** the SaaS lifespan pins it with `asyncio.set_event_loop(asyncio.get_running_loop())` at startup — do not remove that line. The desktop tool is immune (it runs the monitor via `asyncio.run()`, which already sets the thread's loop). Symptom: connects fine ("Conectado"), then only "No response received"; a one-shot script via `asyncio.run` works, so it looks like flakiness. The `run_proto_event was never awaited` warning spam is the same root cause and is harmless (we poll, we don't rely on broadcasts). Caught live; see [[Log/2026-08-15 — Native Rust+ pairing]].

## Pairing

How to obtain the IDs the library needs: [[Rust+ pairing]].
