---
title: Herramienta desktop
tags:
  - desktop
  - rustyalarm
---

# Herramienta desktop

La app original: un solo usuario, suena en **esta** PC. Precede al [[Servicio de suscripción]] y sigue viva e independiente.

## Piezas

| Archivo | Rol |
|---|---|
| `core.py` | Toda la lógica: rutas, config, `AlarmMonitor` (hilo + asyncio). Importa sin efectos |
| `webapp.py` | Panel local con `http.server` en `127.0.0.1:8765` |
| `rust.py` | Versión consola sobre el mismo `AlarmMonitor` |
| `web/index.html` | Página única del panel, sin build |
| `alarma.wav` | Sonido de alarma |

## Correr

```bash
python webapp.py          # panel local, abre el navegador
python rust.py            # modo consola
```

## Build (PyInstaller)

```bash
pyinstaller rust.spec       # dist/rust/rust.exe
pyinstaller webapp.spec     # dist/rust-panel/rust-panel.exe
```

> [!warning] `config.json` no se empaqueta
> `_MEIPASS` es un temp de solo lectura que se borra al cerrar. La config tiene que ser editable, así que vive junto al `.exe`. `alarma.wav` sí se empaqueta como fallback; si el usuario deja su propio `alarma.wav` al lado del exe, `core.sound_path()` prefiere ese.

## Solo Windows

`winsound` maneja el sonido. Se importa defensivamente en `core.py` pero no hay fallback en otro SO. El [[Servicio de suscripción]] no tiene sonido y corre en cualquier lado.

## Emparejar los datos

Los mismos cuatro datos (IP, puerto, Steam ID, player token) + entity ID que el servicio. Cómo obtenerlos: [[Rust+ y emparejamiento]].
