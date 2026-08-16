---
title: Rust+ pairing
tags:
  - reference
  - rust
aliases:
  - pairing
  - entity ID
  - player token
---

# Rust+ pairing

Where the four server values + the alarm's entity ID (required by [[rustplus]] and the [[Subscription service]]) come from. All of it comes from **pairing in Rust+**, not from any panel.

| Value | Source | Changes when |
|---|---|---|
| `STEAM_ID` (`playerId`) | Your SteamID64 | Never |
| `PLAYER_TOKEN` | **Server** pairing | Every re-pair / server change |
| `IP` / `PORT` | Server pairing (Rust+ port, not the game port) | If the server changes |
| `ALARM_ENTITY_ID` | **Device** pairing (the Smart Alarm) | **Every wipe** |

## How RustyAlarm does it (native, in the wizard)

The [[Subscription service]] wizard captures all of this automatically — the user never types the values (manual entry was removed). Flow:

1. **Vincular con Rust+** → `POST /api/pair/start` registers FCM/Expo server-side (`saas/pairing.py`) and returns a single-use `link_nonce`; the panel opens the Facepunch Steam login in a popup.
2. Our **`extension/`** ("RustyAlarm Link") defines the `ReactNativeWebView` bridge on the Facepunch page, captures the `{SteamId, Token}`, and POSTs it to `/api/pair/link` with the nonce. The backend registers the device and starts an MCS listener.
3. In game: `Esc` → **Rust+** → **Pair with Server** → the notification arrives → the wizard fills ip/port/player_token and auto-advances.
4. Look at the Smart Alarm → **Pair** → the `entityId` notification arrives → the wizard fills it.

> [!important] Why a browser extension is required
> After Steam login, Facepunch hands the token back via `window.ReactNativeWebView.postMessage({SteamId, Token})` — a native-app bridge. It **no longer** puts the token in a redirect URL, so a plain hosted page cannot read it (same-origin policy blocks injecting into the cross-origin popup); only a browser extension, the mobile app, or a `--disable-web-security` browser can. `companion-rust.facepunch.com/app?returnUrl=` does **not** return the token to your site (it 500s). This was verified against `rustplus.js` and the rustplus.py docs — full narrative in [[Pitfalls and fixes]].

> [!note] Log in once, not per alarm
> The FCM credentials are cached in the `pairing_creds` table (`saas/db.py`), so the Steam login only happens the **first** time (or after ~12 days, `REUSE_MAX_AGE`). Later alarms reuse the stored registration and just listen — `/api/pair/start` returns `reused: true` with no login and no extension needed; the user only pairs in-game. "usar otra cuenta de Steam" in the wizard forces a fresh login (`force: true`). The one-time AuthToken is still never stored — only the durable FCM registration is.

## Manual alternatives (not used by our wizard)

The community [RustPlus.py Link Companion](https://chrome.google.com/webstore/detail/rustpluspy-link-companion/gojhnmnggbnflhdcpcemeahejhcimnlf) extension or the terminal tool below produce the same pairing JSON, in case you need the raw values outside the app:

```bash
npx @liamcottle/rustplus.js fcm-register    # Steam login, once
npx @liamcottle/rustplus.js fcm-listen      # leaves it listening; pair in game
```

## Trick: entity ID without pairing

Hit the alarm in game, open the console with `F1`, type `combatlog`. The ID shows up as the hit target. Documented by [[rustplus]].

> [!warning] "not_found" in the log
> The server connects but that alarm no longer exists under that ID → typical after a wipe. Re-pair the device and update `ALARM_ENTITY_ID`.

## Sources

- [rplus — Getting Player Details](https://rplus.ollieee.xyz/getting-started/getting-player-details.md)
- [rplus — FCM Listener](https://rplus.ollieee.xyz/getting-started/getting-player-details/fcm-listener.md)
- [rplus — Getting Entity IDs](https://rplus.ollieee.xyz/getting-started/getting-player-details/getting-entity-ids.md)
- [liamcottle/rustplus.js (FCM tool)](https://github.com/liamcottle/rustplus.js)
