---
title: rustplus
tags:
  - referencia
  - dependencia
aliases:
  - rustplus.py
  - RustSocket
---

# rustplus (librería Python)

Wrapper de la API de Rust+ que usan **ambos** productos ([[Arquitectura]]). Versión fijada: **6.0.9** (en `requirements.txt`).

- Repo: [github.com/olijeffers0n/rustplus](https://github.com/olijeffers0n/rustplus)
- Docs: [rplus.ollieee.xyz](https://rplus.ollieee.xyz)
- PyPI: [pypi.org/project/rustplus](https://pypi.org/project/rustplus/)

## API base

```python
from rustplus import RustSocket, ServerDetails
socket = RustSocket(ServerDetails(ip, port, player_id, player_token))
await socket.connect()
entity = await socket.get_entity_info(entity_id)
```

Esta forma es de la 6.x y difiere de versiones viejas. Fijar a 6.x al reinstalar.

- [Docs — RustSocket](https://rplus.ollieee.xyz/getting-started/rustsocket.md)
- [Docs — Getting Entity Information](https://rplus.ollieee.xyz/api-methods/getting-entity-information.md)

## Trampas (todas verificadas contra la 6.0.9)

> [!bug] Señala fallos por valor de retorno, no por excepción
> - `socket.connect()` devuelve `False` (no lanza) cuando el server no responde. **Hay que chequear el bool.**
> - `socket.get_entity_info()` devuelve un `RustError` (con `.reason`) ante entity mala/wipeada. `isinstance(entity, RustError)` antes de tocar `.value`.
> - Un socket muerto sigue devolviendo `RustError`/`None` sin lanzar. El monitor cuenta respuestas fallidas seguidas (`RECONNECT_AFTER`) para decidir reconectar. Ver [[Servicio de suscripción]].

> [!bug] Fuga de handlers de logging
> Agrega un `StreamHandler` DEBUG nuevo al logger `rustplus.py` en **cada** construcción de `RustSocket()`. Construir uno por reconexión los acumula sin techo (memoria + log duplicado). `monitor.quiet_rustplus_logger()` los limpia. Ojo: el logger se llama `rustplus.py`, no `rustplus`.

## Emparejamiento

Cómo obtener los IDs que pide la librería: [[Rust+ y emparejamiento]].
