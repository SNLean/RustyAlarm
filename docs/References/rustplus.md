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

## Pairing

How to obtain the IDs the library needs: [[Rust+ pairing]].
