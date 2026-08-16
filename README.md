# RustyAlarm

Avisos de raid para [Rust](https://rust.facepunch.com/). RustyAlarm vigila tu **Smart Alarm** a través de la API de Rust+ y te avisa apenas se dispara — para que no te enteres del ataque cuando ya es tarde.

> Servicio no afiliado a Facepunch Studios.

## Dos productos en un repo

Comparten únicamente la librería [`rustplus`](https://github.com/olijeffers0n/rustplus). Un cambio en uno no toca el otro.

| Producto | Qué es | Carpeta |
| --- | --- | --- |
| **Servicio de suscripción** | Webapp multiusuario hosteada: login con Steam, alarmas por usuario, aviso a Discord. Es el producto. | `saas/`, `saas/templates/` |
| **Herramienta de escritorio** | App local de un solo usuario que suena en la PC (`winsound`). El origen del proyecto. | `core.py`, `webapp.py`, `rust.py`, `web/` |

## Cómo empezar

Requisitos: Python 3.14, Windows para la herramienta de escritorio (usa `winsound`); el servicio corre en cualquier SO.

### Servicio de suscripción

```bash
pip install -r requirements.txt
python -m saas
```

Sirve en `http://127.0.0.1:8000/`. Se configura por variables de entorno `RUSTALARM_*` (ver `.env.example` y `saas/config.py`). Para producción en un VPS con nginx + HTTPS, seguí **[deploy/DEPLOY.md](deploy/DEPLOY.md)**.

> **Un solo worker, a propósito.** El monitor guarda estado en memoria (una corrutina por alarma); con varios workers cada uno abriría todas las alarmas y duplicaría los avisos. No uses gunicorn multi-proceso ni `--workers`.

### Herramienta de escritorio

```bash
python webapp.py     # panel local en http://127.0.0.1:8765/
python rust.py       # modo consola
```

Se configura con `config.json` (ver `config.example.json`). Build con PyInstaller: `pyinstaller webapp.spec` / `pyinstaller rust.spec`.

## Conseguir los datos de Rust+

Ambos productos piden IP, puerto Rust+, Steam ID, player token y el entity ID de la alarma. Todos salen de **parear Rust+ en el juego** (extensión de Chrome o CLI). Guía paso a paso: [docs/Referencias/Rust+ y emparejamiento](docs/Referencias/Rust%2B%20y%20emparejamiento.md). El servicio además trae un asistente in-app que te guía dato por dato.

## Documentación

- **[docs/](docs/)** — vault de Obsidian con toda la documentación del proyecto: arquitectura, decisiones, seguridad, deploy, referencias a las docs oficiales de cada dependencia, y una bitácora por sesión. Abrí la carpeta como vault en Obsidian, o leé el índice en [docs/Home.md](docs/Home.md).
- **[deploy/DEPLOY.md](deploy/DEPLOY.md)** — puesta en producción en VPS Ubuntu + nginx.
- **CLAUDE.md** — guía para agentes de código que trabajen en el repo.

## Stack

- **Servicio**: FastAPI + Uvicorn, SQLite, Jinja2, httpx, login Steam OpenID (sin API key), aviso por Discord webhook. Front en HTML/CSS/JS vanilla.
- **Escritorio**: `http.server` de la biblioteca estándar + `winsound`.
- **Común**: `rustplus` 6.0.9.

## Seguridad y datos

- Los secretos (`config.json`, la base `saas_data/`, `.env`) están en `.gitignore` y **nunca** se commitean.
- El servicio aísla a cada usuario por su Steam ID, valida entradas, protege contra CSRF y XSS, y setea CSP + `X-Frame-Options`. Detalle en [docs/Seguridad y revisión](docs/Seguridad%20y%20revisi%C3%B3n.md).

## Licencia

Sin licencia pública definida. Repositorio privado.
