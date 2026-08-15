# Deploy en VPS Ubuntu + nginx

Guía para poner el servicio de suscripción (`saas/`) en producción detrás de nginx con HTTPS. El desktop tool (`webapp.py`, `rust.py`) no se despliega; esto es solo el servicio.

Reemplazá `TU_DOMINIO` por tu dominio real (por ejemplo `alarmas.midominio.com`) en todos los pasos.

## Antes de empezar

- Un VPS con Ubuntu (22.04 o 24.04) y acceso `sudo`.
- Un dominio apuntando (registro **A**) a la IP del VPS.
- El repo es **privado**: el VPS necesita credenciales para clonarlo. Lo más limpio es una **deploy key** de solo lectura (más abajo).

## Restricción de arquitectura (importante)

El servicio corre en **un solo proceso, un solo worker**. El monitor guarda el estado en memoria (una corrutina por alarma); con varios workers cada uno abriría todas las alarmas y mandaría alertas de Discord duplicadas. El `rustyalarm.service` arranca `python -m saas`, que es single-worker a propósito. **No** lo cambies a gunicorn con varios procesos ni agregues `--workers`.

## 1. Paquetes del sistema

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx git
```

## 2. Usuario de servicio y carpeta

```bash
sudo useradd --system --create-home --home-dir /opt/rustyalarm --shell /usr/sbin/nologin rustyalarm
```

## 3. Clonar el repo (privado)

Generá una deploy key en el VPS y cargala en GitHub:

```bash
sudo -u rustyalarm ssh-keygen -t ed25519 -f /opt/rustyalarm/.ssh/id_ed25519 -N ""
sudo cat /opt/rustyalarm/.ssh/id_ed25519.pub
```

Copiá esa clave pública en GitHub: repo **RustyAlarm → Settings → Deploy keys → Add deploy key** (solo lectura, sin write). Después:

```bash
sudo -u rustyalarm git clone git@github.com:SNLean/RustyAlarm.git /opt/rustyalarm/app
```

(Si preferís HTTPS con un token en vez de deploy key, también sirve; la deploy key evita manejar tokens.)

## 4. Entorno virtual y dependencias

```bash
cd /opt/rustyalarm/app
sudo -u rustyalarm python3 -m venv /opt/rustyalarm/.venv
sudo -u rustyalarm /opt/rustyalarm/.venv/bin/pip install --upgrade pip
sudo -u rustyalarm /opt/rustyalarm/.venv/bin/pip install -r requirements.txt
```

## 5. Configuración (.env)

```bash
sudo -u rustyalarm cp .env.example /opt/rustyalarm/app/.env
sudo -u rustyalarm nano /opt/rustyalarm/app/.env
```

Valores para producción:

```
RUSTALARM_BASE_URL=https://TU_DOMINIO
RUSTALARM_HOST=127.0.0.1
RUSTALARM_PORT=8000
RUSTALARM_ADMIN_STEAM_ID=TU_STEAMID64
RUSTALARM_MAX_ALARMS=3
```

- `RUSTALARM_BASE_URL` **tiene que ser** `https://TU_DOMINIO`. De ahí salen el retorno del login de Steam, la marca `Secure` de las cookies y el chequeo anti-CSRF. Si no coincide con el dominio real, el login de Steam falla.
- `RUSTALARM_HOST=127.0.0.1`: uvicorn escucha solo local; nginx lo expone al mundo. No lo pongas en `0.0.0.0`.
- `RUSTALARM_ADMIN_STEAM_ID`: tu SteamID64. Es quien ve `/admin`.

El `.service` ya asume esta estructura: código en `/opt/rustyalarm/app`, venv en `/opt/rustyalarm/.venv`, `.env` y `saas_data/` dentro de `app/`. Si clonaste en esas rutas (paso 3 y 4), no tenés que tocar nada.

## 6. Servicio systemd

```bash
sudo cp deploy/rustyalarm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rustyalarm
sudo systemctl status rustyalarm
```

Verificar que responde local antes de nginx:

```bash
curl -I http://127.0.0.1:8000/
```

## 7. nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/rustyalarm
sudo sed -i 's/TU_DOMINIO/alarmas.midominio.com/' /etc/nginx/sites-available/rustyalarm
sudo ln -s /etc/nginx/sites-available/rustyalarm /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

## 8. HTTPS con Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d TU_DOMINIO
```

certbot agrega el bloque `443` y el redirect de `80` a `443` solo. Confirmá que `RUSTALARM_BASE_URL` en `.env` sea `https://TU_DOMINIO` y reiniciá:

```bash
sudo systemctl restart rustyalarm
```

Entrá a `https://TU_DOMINIO`, login con Steam, y `https://TU_DOMINIO/admin` para gestionar planes.

## Actualizar a una versión nueva

```bash
cd /opt/rustyalarm/app
sudo -u rustyalarm git pull
sudo -u rustyalarm /opt/rustyalarm/.venv/bin/pip install -r requirements.txt
sudo systemctl restart rustyalarm
```

## Logs y datos

- Logs del servicio: `journalctl -u rustyalarm -f`
- Base de datos: `/opt/rustyalarm/app/saas_data/rustalarm.db`. Está en `.gitignore`; respaldala aparte. **Backup:** `sqlite3 /opt/rustyalarm/app/saas_data/rustalarm.db ".backup copia.db"`.
