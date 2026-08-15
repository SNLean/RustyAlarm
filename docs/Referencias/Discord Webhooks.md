---
title: Discord Webhooks
tags:
  - referencia
  - notificaciones
---

# Discord Webhooks

El canal de aviso del [[Servicio de suscripción]] (ver [[Decisiones de producto]]). Implementado en `saas/notify.py` con [[FastAPI y Uvicorn|httpx]].

## Cómo lo obtiene el usuario

Canal de Discord → **Editar canal** → **Integraciones** → **Webhooks** → **Nuevo webhook** → **Copiar URL**. Esa URL va al campo del panel.

## Cómo lo usa el servicio

`POST` a la URL del webhook con un `embed` (título, servidor, timestamp). Al dispararse la alarma manda color rojo; el botón "Probar Discord" del panel manda uno verde de prueba.

> [!tip] Validación de la URL
> `validate_alarm` (`saas/db.py`) solo acepta URLs que empiezan con los prefijos oficiales de webhook de Discord (`discord.com` / `discordapp.com` / subdominios `canary`/`ptb`). Corta que se pegue cualquier URL. Ver [[Seguridad y revisión]].

## Formato del payload

Objeto con `embeds: [...]`. Cada embed: `title`, `description`, `color` (entero), `fields`, `footer`, `timestamp` (ISO 8601).

## Fuentes

- [Discord Developer — Execute Webhook](https://discord.com/developers/docs/resources/webhook#execute-webhook)
- [Discord Developer — Embed Object](https://discord.com/developers/docs/resources/message#embed-object)
- [Discord Support — Intro to Webhooks](https://support.discord.com/hc/en-us/articles/228383668)
