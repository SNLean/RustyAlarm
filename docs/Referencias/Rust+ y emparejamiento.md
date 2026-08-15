---
title: Rust+ y emparejamiento
tags:
  - referencia
  - rust
aliases:
  - emparejamiento
  - pairing
  - entity ID
  - player token
---

# Rust+ y emparejamiento

De dónde salen los cuatro datos de servidor + el entity ID de la alarma que piden [[rustplus]] y el [[Servicio de suscripción]]. Todo viene del **pareo de Rust+**, no de ningún panel.

| Dato | Origen | Cambia cuando |
|---|---|---|
| `STEAM_ID` (`playerId`) | Tu SteamID64 | Nunca |
| `PLAYER_TOKEN` | Pareo **de servidor** | Cada re-pareo / cambio de server |
| `IP` / `PORT` | Pareo de servidor (puerto Rust+, no el de juego) | Si cambia el server |
| `ALARM_ENTITY_ID` | Pareo **del dispositivo** (la Smart Alarm) | **En cada wipe** |

## Método fácil (extensión de Chrome)

1. Instalar [RustPlus.py Link Companion](https://chrome.google.com/webstore/detail/rustpluspy-link-companion/gojhnmnggbnflhdcpcemeahejhcimnlf) (la que recomienda la doc oficial).
2. Click en el icono → login con Steam en Facepunch → redirige a una página con credenciales.
3. Dejar "listen for notifications" abierto.
4. En el juego: `Esc` → **Rust+** → **Pair with Server** → llega `ip`, `port`, `playerId`, `playerToken`.
5. Mirar la Smart Alarm → **Pair** → llega `entityId`.

## Método por terminal (alternativa)

Requiere Node.js:

```bash
npx @liamcottle/rustplus.js fcm-register    # login Steam, una vez
npx @liamcottle/rustplus.js fcm-listen      # deja escuchando; pareá en el juego
```

## Truco: entity ID sin parear

Golpeá la alarma en el juego, abrí consola con `F1`, escribí `combatlog`. El ID aparece como objetivo del golpe. Documentado por [[rustplus]].

> [!warning] "not_found" en el log
> El server conecta pero esa alarma ya no existe con ese ID → típico post-wipe. Repetir el pareo del dispositivo y actualizar el `ALARM_ENTITY_ID`.

## Fuentes

- [rplus — Getting Player Details](https://rplus.ollieee.xyz/getting-started/getting-player-details.md)
- [rplus — FCM Listener](https://rplus.ollieee.xyz/getting-started/getting-player-details/fcm-listener.md)
- [rplus — Getting Entity IDs](https://rplus.ollieee.xyz/getting-started/getting-player-details/getting-entity-ids.md)
- [liamcottle/rustplus.js (herramienta FCM)](https://github.com/liamcottle/rustplus.js)
