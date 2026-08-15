---
title: Servicio de suscripción
tags:
  - saas
  - rustyalarm
---

# Servicio de suscripción (`saas/`)

Webapp multiusuario. Un proceso [[FastAPI y Uvicorn|uvicorn]], un solo event loop; las rutas web y todos los monitores de alarma lo comparten.

## Módulos

| Archivo | Rol |
|---|---|
| `saas/app.py` | Rutas FastAPI, middleware de headers, sesión, API de alarmas, admin |
| `saas/db.py` | SQLite (sync + `RLock`), validación de alarmas |
| `saas/monitor.py` | `Manager` + `AlarmRunner`: una corrutina por alarma |
| `saas/steam.py` | Login [[Steam OpenID]] (sin API key) |
| `saas/notify.py` | Aviso a [[Discord Webhooks]] |
| `saas/config.py` | Config por variables de entorno `RUSTALARM_*` |
| `saas/templates/` | Jinja2: landing, panel, admin |

## Flujo del usuario

1. Landing (`/`) → botón **Entrar con Steam** → [[Steam OpenID]].
2. Panel (`/panel`): CRUD de alarmas, estado en vivo (polling cada 2 s a `/api/alarms`), botón "Probar Discord". El alta usa un **asistente guiado por pasos** (onboarding + guías in-app); ver [[Registro/2026-08-15 — Asistente de alta guiado]].
3. Admin (`/admin`, solo el dueño): pausar/activar cuentas. Ver [[Decisiones de producto]] sobre por qué es manual.

## El monitor

`Manager` reconcilia la tabla `alarms` contra las corrutinas vivas: compara `updated_at`, cancela las obsoletas, arranca las que faltan. Se llama tras cada CRUD y cada 30 s.

`AlarmRunner`:
- Backoff exponencial al fallar la conexión (15 s → 300 s).
- Cuenta respuestas fallidas seguidas (`RECONNECT_AFTER`) para detectar socket muerto, porque [[rustplus]] no lanza excepción cuando el socket cae.
- Cooldown para no repetir el aviso de Discord.
- El estado vivo (status, logs) es **solo memoria**: reiniciar lo pierde, a propósito.

> [!note] `active_alarms()` filtra por plan
> El query une `alarms` con `users.plan_active`. Pausar un usuario detiene sus alarmas sin código extra. Ver [[Decisiones de producto]].

## Base de datos

SQLite en `saas_data/rustalarm.db`, modo WAL, un `RLock` global. Las corrutinas la tocan vía `asyncio.to_thread`. Tres tablas: `users`, `sessions`, `alarms`. Está en `.gitignore`.

## Seguridad

Invariantes en [[Seguridad y revisión]]: `same_origin()` (CSRF) en toda ruta que muta, queries scopeadas por `steam_id` (aislamiento entre usuarios), `state` anti-CSRF en el login, escape en el panel, headers CSP + `X-Frame-Options`.
