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

## Easy method (Chrome extension)

1. Install [RustPlus.py Link Companion](https://chrome.google.com/webstore/detail/rustpluspy-link-companion/gojhnmnggbnflhdcpcemeahejhcimnlf) (the one the official docs recommend).
2. Click the icon → sign in with Steam on Facepunch → it redirects to a credentials page.
3. Leave "listen for notifications" open.
4. In game: `Esc` → **Rust+** → **Pair with Server** → `ip`, `port`, `playerId`, `playerToken` arrive.
5. Look at the Smart Alarm → **Pair** → `entityId` arrives.

## Terminal method (alternative)

Requires Node.js:

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
