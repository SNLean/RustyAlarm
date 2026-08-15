---
title: FastAPI y Uvicorn
tags:
  - referencia
  - dependencia
  - stack
---

# FastAPI y Uvicorn

Stack del [[Servicio de suscripción]]. Versiones fijadas en `requirements.txt`.

| Paquete | Versión | Rol |
|---|---|---|
| fastapi | 0.141.1 | Framework de rutas / API |
| uvicorn[standard] | 0.52.3 | Servidor ASGI |
| jinja2 | 3.1.6 | Templates (landing, panel, admin) |
| httpx | 0.28.1 | Cliente HTTP async (Steam verify, Discord) |
| python-multipart | 0.0.32 | Parsing de formularios |

## Notas de implementación

- La app se crea con `docs_url=None, redoc_url=None, openapi_url=None`: sin docs autogeneradas expuestas.
- Un `@app.middleware("http")` agrega los headers de seguridad ([[Seguridad y revisión]]).
- `lifespan` arranca el `Manager` del monitor y lo apaga limpio.

> [!note] Detrás de nginx
> `saas/__main__.py` corre uvicorn con `proxy_headers=True` y `forwarded_allow_ips` para confiar en los `X-Forwarded-Proto/For` que manda [[nginx y systemd|nginx]]. Ver [[Deploy en VPS]].

> [!warning] Un solo worker
> Ver [[Arquitectura]]. El estado del monitor es en memoria; multi-worker duplica todo.

## Fuentes

- [FastAPI](https://fastapi.tiangolo.com/)
- [FastAPI — Behind a Proxy](https://fastapi.tiangolo.com/advanced/behind-a-proxy/)
- [Uvicorn](https://www.uvicorn.org/)
- [Uvicorn — Deployment](https://www.uvicorn.org/deployment/)
- [Uvicorn — Settings (proxy-headers)](https://www.uvicorn.org/settings/)
- [Jinja2](https://jinja.palletsprojects.com/)
- [HTTPX](https://www.python-httpx.org/)
