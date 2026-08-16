---
title: Desktop tool
tags:
  - desktop
  - rustyalarm
---

# Desktop tool

The original app: single user, plays sound on **this** PC. It predates the [[Subscription service]] and stays alive and independent.

## Pieces

| File | Role |
|---|---|
| `core.py` | All the logic: paths, config, `AlarmMonitor` (thread + asyncio). Imports with no side effects |
| `webapp.py` | Local `http.server` panel at `127.0.0.1:8765` |
| `rust.py` | Console version over the same `AlarmMonitor` |
| `web/index.html` | Single-page panel, no build step |
| `alarma.wav` | Alarm sound |

## Run

```bash
python webapp.py     # local panel, opens the browser
python rust.py       # console mode
```

## Build (PyInstaller)

```bash
pyinstaller rust.spec       # dist/rust/rust.exe
pyinstaller webapp.spec     # dist/rust-panel/rust-panel.exe
```

> [!warning] `config.json` is not bundled
> `_MEIPASS` is a read-only temp dir wiped on exit. The config must be editable, so it lives next to the `.exe`. `alarma.wav` is bundled as a fallback; if the user drops their own `alarma.wav` next to the exe, `core.sound_path()` prefers it.

## Windows only

`winsound` drives the sound. It is imported defensively in `core.py` but there is no fallback on other OSes. The [[Subscription service]] has no sound and runs anywhere.

## Pairing the data

Same four values (IP, Rust+ port, Steam ID, player token) + entity ID as the service. How to get them: [[Rust+ pairing]].
