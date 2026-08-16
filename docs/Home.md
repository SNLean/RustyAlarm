---
title: RustyAlarm — Índice
tags:
  - moc
  - rustyalarm
aliases:
  - Home
  - MOC
  - Índice
---

# RustyAlarm 🔔

Servicio que vigila una **Smart Alarm de Rust** (el juego) vía la API de Rust+ y avisa cuando se dispara. Dos productos en un repo, comparten la librería [[rustplus]].

> [!info] Repositorio
> Privado: [github.com/SNLean/RustyAlarm](https://github.com/SNLean/RustyAlarm) · rama `main`

## Mapa

- [[Arquitectura]] — cómo encaja todo
- [[Servicio de suscripción]] — la webapp multiusuario (`saas/`)
- [[Herramienta desktop]] — la app local original (`webapp.py`, `rust.py`)
- [[Decisiones de producto]] — qué se eligió y por qué
- [[Seguridad y revisión]] — hallazgos de la revisión adversarial y sus fixes
- [[Deploy en VPS]] — Ubuntu + nginx + HTTPS

## Referencias (docs oficiales)

- [[rustplus]] — librería Python de Rust+
- [[Rust+ y emparejamiento]] — de dónde salen Steam ID, player token, entity ID
- [[Steam OpenID]] — login con Steam
- [[FastAPI y Uvicorn]] — stack del servicio
- [[nginx y systemd]] — correr en producción
- [[Discord Webhooks]] — el canal de aviso
- [[Skills de diseño y animación]] — herramientas para pulir UI/animación

## Registro de sesiones

- [[Registro/2026-08-15 — Del script al servicio]]
- [[Registro/2026-08-15 — Skills de diseño y animación]]
- [[Registro/2026-08-15 — Asistente de alta guiado]]
- [[Registro/2026-08-15 — Rediseño del front]]

## Meta

- [[Cómo mantener este vault]]

> [!tip] Cómo se mantiene este vault
> Ver [[Cómo mantener este vault]]. Regla corta: cada sesión de trabajo deja una nota en `Registro/` con fecha, qué cambió y **weblinks** a las fuentes usadas; los datos duraderos se destilan en las notas temáticas de arriba.
