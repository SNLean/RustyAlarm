---
title: Steam OpenID
tags:
  - reference
  - auth
aliases:
  - Steam login
  - OpenID
---

# Steam OpenID

The [[Subscription service]] login. **No Steam API key required** — plain OpenID 2.0. Implemented in `saas/steam.py`.

## Flow

1. `login_url(state)` sends the user to `https://steamcommunity.com/openid/login` with `openid.mode=checkid_setup`. The `state` is embedded in `return_to` (which Steam signs).
2. Steam redirects to `BASE_URL/auth/steam/return` with the signature.
3. `verify()` re-posts the params to Steam with `mode=check_authentication`; Steam replies `is_valid:true`. The SteamID64 comes from `claimed_id` (an anchored 17-digit regex).

> [!warning] `BASE_URL` must be the exact public domain
> `return_to` and `realm` are built from `BASE_URL`. If it does not match the real domain (e.g. left as `http://127.0.0.1` in production), login fails. See [[VPS deployment]].

> [!tip] Login anti-CSRF
> The `state` is stored in a cookie at `/login` and compared on return with `secrets.compare_digest`. It blocks an attacker from logging you in with their account. See [[Security review]].

## Sources

- [Steamworks — Steam Web API / OpenID](https://partner.steamgames.com/doc/features/auth)
- [Steam Community — Developer](https://steamcommunity.com/dev)
- [OpenID 2.0 (spec)](https://openid.net/specs/openid-authentication-2_0.html)
