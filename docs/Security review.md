---
title: Security review
tags:
  - security
  - review
  - rustyalarm
date: 2026-08-15
---

# Security review

The [[Subscription service]] code went through an adversarial review (31 agents, four dimensions: authorization, concurrency, data correctness, XSS). It confirmed 19 issues; 16 were fixed and verified live. The other 3 are [[Product decisions#Deliberately left as is (not bugs)|conscious decisions]].

## Invariants that must not be weakened

> [!danger] Touching this breaks security
> - Every mutating route calls `same_origin()` (CSRF via Origin/Referer).
> - Every alarm query is scoped by the session's `steam_id` (tenant isolation). That is the **entire** multi-tenant story.
> - [[Steam OpenID]] login binds a `state` (cookie ↔ signed `return_to`) against login-CSRF.
> - A middleware sets CSP + `X-Frame-Options: DENY` (anti-clickjacking).

## Fixes applied

### Panel XSS
`cardHtml` builds HTML as strings and assigns it via `innerHTML`. Every interpolated field (name, IP, detail, log) is escaped with `esc()`. Verified: an `<img onerror>` payload renders as text, does not execute.

### Secrets out of the DOM
It used to serialize the whole alarm object (with `player_token` and webhook) into an `onclick`. Now editing reads from an in-memory map (`alarmsById`); nothing sensitive enters the HTML.

### Login-CSRF / session fixation
`/login` generates a `state`, puts it in a cookie and embeds it in `return_to` (which Steam signs). On return they are compared with `secrets.compare_digest`.

### Hardened validation (`validate_alarm`)
- `port`: `str.isascii() and str.isdigit()` — the Arabic digit `٤` passes `isdigit()` but is not a valid port.
- Non-finite floats rejected (`inf`/`nan`).
- `ip`: host characters only, with a length cap — cuts payloads.
- Integers outside the signed 32-bit range rejected.

### Functional [[rustplus]] bugs
- `connect()` returns `False` without raising → it used to falsely show "running" with the server down; now the bool is checked.
- A dead socket does not raise → count consecutive failed responses to reconnect.
- Log-handler leak → `quiet_rustplus_logger()` clears them after each `RustSocket()`.

## Sources

- [OWASP — Cross-Site Request Forgery](https://owasp.org/www-community/attacks/csrf)
- [OWASP — Cross Site Scripting (XSS)](https://owasp.org/www-community/attacks/xss/)
- [MDN — Content-Security-Policy](https://developer.mozilla.org/docs/Web/HTTP/Headers/Content-Security-Policy)
- [MDN — X-Frame-Options](https://developer.mozilla.org/docs/Web/HTTP/Headers/X-Frame-Options)
- [MDN — SameSite cookies](https://developer.mozilla.org/docs/Web/HTTP/Headers/Set-Cookie/SameSite)
