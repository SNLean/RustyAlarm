---
title: Seguridad y revisión
tags:
  - seguridad
  - revision
  - rustyalarm
date: 2026-08-15
---

# Seguridad y revisión

El código del [[Servicio de suscripción]] pasó por una revisión adversarial (31 agentes, cuatro dimensiones: autorización, concurrencia, correctitud de datos, XSS). Confirmó 19 problemas; se corrigieron 16 y se verificaron en vivo. Los otros 3 son [[Decisiones de producto#Cosas dejadas a propósito|decisiones conscientes]].

## Invariantes que no se deben debilitar

> [!danger] Tocar esto rompe la seguridad
> - Toda ruta que muta llama `same_origin()` (CSRF por Origin/Referer).
> - Toda query de alarmas se scopea por el `steam_id` de la sesión (aislamiento entre usuarios). Es **toda** la historia multi-tenant.
> - El login de [[Steam OpenID]] ata un `state` (cookie ↔ `return_to` firmado) contra login-CSRF.
> - Un middleware pone CSP + `X-Frame-Options: DENY` (anti-clickjacking).

## Fixes aplicados

### XSS en el panel
`cardHtml` arma HTML como strings y lo asigna por `innerHTML`. Todo campo interpolado (nombre, IP, detalle, log) se escapa con `esc()`. Probado: un payload `<img onerror>` queda como texto, no ejecuta.

### Secretos fuera del DOM
Antes se serializaba el objeto de alarma completo (con `player_token` y webhook) en un `onclick`. Ahora la edición lee de un mapa en memoria (`alarmsById`); nada sensible entra al HTML.

### Login-CSRF / fijación de sesión
`/login` genera `state`, lo pone en cookie y lo mete en `return_to` (que Steam firma). Al volver se comparan con `secrets.compare_digest`.

### Validación endurecida (`validate_alarm`)
- `port`: `str.isascii() and str.isdigit()` — el dígito árabe `٤` pasa `isdigit()` pero no sirve de puerto.
- floats no finitos rechazados (`inf`/`nan`).
- `ip`: solo caracteres de host, con límite de longitud — corta payloads.
- enteros fuera del rango de 32 bits con signo rechazados.

### Bugs funcionales de [[rustplus]]
- `connect()` devuelve `False` sin lanzar → antes marcaba "running" en falso con el server caído; ahora se chequea el bool.
- Socket muerto no lanza excepción → se cuenta respuestas fallidas seguidas para reconectar.
- Fuga de handlers de log → `quiet_rustplus_logger()` los limpia tras cada `RustSocket()`.

## Fuentes

- [OWASP — Cross-Site Request Forgery](https://owasp.org/www-community/attacks/csrf)
- [OWASP — Cross Site Scripting (XSS)](https://owasp.org/www-community/attacks/xss/)
- [MDN — Content-Security-Policy](https://developer.mozilla.org/docs/Web/HTTP/Headers/Content-Security-Policy)
- [MDN — X-Frame-Options](https://developer.mozilla.org/docs/Web/HTTP/Headers/X-Frame-Options)
- [MDN — SameSite cookies](https://developer.mozilla.org/docs/Web/HTTP/Headers/Set-Cookie/SameSite)
