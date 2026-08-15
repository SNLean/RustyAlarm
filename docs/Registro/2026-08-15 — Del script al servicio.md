---
title: 2026-08-15 — Del script al servicio
tags:
  - registro
  - sesion
date: 2026-08-15
---

# 2026-08-15 — Del script al servicio

Bitácora de la sesión donde RustyAlarm pasó de un script suelto a un servicio hosteado con repo y deploy. Contexto duradero destilado en las notas temáticas ([[Home]]).

## Qué se hizo

1. **CLAUDE.md** inicial del repo (guía para agentes).
2. **Refactor del desktop**: `core.py` sin efectos al importar; `webapp.py` (panel local) + `rust.py` (consola) sobre el mismo `AlarmMonitor`. Ver [[Herramienta desktop]]. De paso se arreglaron bugs viejos: `last_state` que no se actualizaba (sonaba en cada poll), `COOLDOWN` sin aplicar, rutas relativas al CWD.
3. **Instructivos de emparejamiento** en el panel, alineados con la doc oficial. Ver [[Rust+ y emparejamiento]].
4. **Servicio de suscripción** (`saas/`): login [[Steam OpenID]], alarmas por usuario en SQLite, monitor asyncio, aviso [[Discord Webhooks]], admin. Ver [[Servicio de suscripción]] y [[Arquitectura]].
5. **Revisión adversarial** (31 agentes): 19 hallazgos, 16 corregidos y verificados en vivo. Ver [[Seguridad y revisión]].
6. **Git**: repo privado [SNLean/RustyAlarm](https://github.com/SNLean/RustyAlarm), `.gitignore` que excluye secretos, `requirements.txt`, `.env.example`, `config.example.json`. Se resolvió un lío de credenciales (git estaba como `BriYlean`, el repo es de `SNLean`).
7. **Deploy** para VPS Ubuntu + nginx: `deploy/rustyalarm.service`, `deploy/nginx.conf`, `deploy/DEPLOY.md`. Ver [[Deploy en VPS]].
8. **Este vault de Obsidian** en `docs/`.

## Decisiones tomadas

Detalle en [[Decisiones de producto]]: sin pagos aún (plan manual), aviso por Discord, login Steam, hosting en VPS.

## Pendiente

- Correr los pasos de `deploy/DEPLOY.md` en el VPS real.
- Integrar proveedor de pago (manejará `plan_active`).
- Opcional: `deploy/backup.sh` por cron, script de update de una línea.

## Fuentes consultadas esta sesión

- [rustplus (repo)](https://github.com/olijeffers0n/rustplus) · [docs](https://rplus.ollieee.xyz)
- [rplus — Getting Player Details](https://rplus.ollieee.xyz/getting-started/getting-player-details.md)
- [liamcottle/rustplus.js](https://github.com/liamcottle/rustplus.js)
- [FastAPI](https://fastapi.tiangolo.com/) · [Uvicorn deployment](https://www.uvicorn.org/deployment/)
- [Certbot](https://certbot.eff.org/instructions)
