---
title: Steam OpenID
tags:
  - referencia
  - auth
aliases:
  - login con Steam
  - OpenID
---

# Steam OpenID

Login del [[Servicio de suscripción]]. **No requiere API key de Steam** — usa OpenID 2.0 puro. Implementado en `saas/steam.py`.

## Flujo

1. `login_url(state)` manda al usuario a `https://steamcommunity.com/openid/login` con `openid.mode=checkid_setup`. El `state` va dentro de `return_to` (que Steam firma).
2. Steam redirige a `BASE_URL/auth/steam/return` con la firma.
3. `verify()` reenvía los parámetros a Steam con `mode=check_authentication`; Steam responde `is_valid:true`. El SteamID64 sale del `claimed_id` (regex de 17 dígitos anclado).

> [!warning] `BASE_URL` tiene que ser el dominio público exacto
> El `return_to` y el `realm` se construyen desde `BASE_URL`. Si no coincide con el dominio real (por ejemplo, quedó en `http://127.0.0.1` en producción), el login falla. Ver [[Deploy en VPS]].

> [!tip] Anti-CSRF del login
> El `state` se guarda en cookie en `/login` y se compara al volver con `secrets.compare_digest`. Bloquea que un atacante te loguee con su cuenta. Ver [[Seguridad y revisión]].

## Fuentes

- [Steamworks — Steam Web API / OpenID](https://partner.steamgames.com/doc/features/auth)
- [Steam Community — Developer](https://steamcommunity.com/dev)
- [OpenID 2.0 (spec)](https://openid.net/specs/openid-authentication-2_0.html)
