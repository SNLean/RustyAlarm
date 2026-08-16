"""Rutas FastAPI: landing, login Steam, panel de alarmas y admin.

Arranque: python -m saas
"""

import asyncio
import logging
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import db, pairing, sounds, steam, verify
from .config import ADMIN_STEAM_ID, BASE_URL, MAX_ALARMS, SESSION_COOKIE, SESSION_DAYS
from .monitor import manager
from .notify import send_discord

OAUTH_STATE_COOKIE = "rustalarm_oauth_state"

# Rate limit de la verificacion en vivo: cada verify abre una conexion saliente
# a un ip:port que elige el usuario. Sin freno seria un escaner de puertos a
# pedido. En memoria alcanza: el servicio corre en un solo worker.
VERIFY_MIN_GAP = 4.0          # seg minimos entre verify del mismo usuario
VERIFY_MAX_CONCURRENT = 4     # verify en vuelo en todo el proceso
_verify_last: dict[str, float] = {}
_verify_inflight: set[str] = set()

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


SECURE_COOKIES = BASE_URL.startswith("https://")


@asynccontextmanager
async def lifespan(app):
    # Aviso de config: en un dominio real BASE_URL tiene que ser https, si no
    # las cookies viajan sin Secure y el retorno de Steam falla.
    host = urlparse(BASE_URL).hostname or ""
    if not SECURE_COOKIES and host not in ("127.0.0.1", "localhost", "::1"):
        logging.getLogger("rustalarm").warning(
            "RUSTALARM_BASE_URL=%s no es https y no es local: las cookies NO "
            "seran Secure. En produccion usa https://tu-dominio.", BASE_URL)
    # rustplus despacha el manejo de sus mensajes (incluido el emparejado de
    # respuestas) con asyncio.get_event_loop_policy().get_event_loop().create_task().
    # Bajo uvicorn eso puede resolver a un loop que NO es el que corre, y
    # entonces handle_message nunca ejecuta: cada get_entity_info agota el
    # timeout y devuelve "No response received". Fijamos el loop de la policy al
    # que realmente corre para que esas tareas caigan donde deben.
    asyncio.set_event_loop(asyncio.get_running_loop())
    db.connect()
    await manager.start()
    yield
    await manager.shutdown()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline';"
        " script-src 'self' 'unsafe-inline'; img-src 'self' data:;"
        " connect-src 'self'; frame-ancestors 'none'; base-uri 'none';"
        " form-action 'self' https://steamcommunity.com"
    )
    return response


# ================= HELPERS =================

def current_user(request: Request):
    return db.user_by_session(request.cookies.get(SESSION_COOKIE, ""))


def is_admin(user) -> bool:
    if user is None:
        return False
    return bool(user["is_admin"]) or (
        ADMIN_STEAM_ID and user["steam_id"] == ADMIN_STEAM_ID
    )


def same_origin(request: Request) -> bool:
    """CSRF: los POST/PUT/DELETE tienen que venir de nuestro propio origen."""
    origin = request.headers.get("origin") or request.headers.get("referer") or ""
    if not origin:
        return False
    parsed = urlparse(origin)
    expected = urlparse(BASE_URL)
    return (parsed.scheme, parsed.netloc) == (expected.scheme, expected.netloc)


def need_login():
    return JSONResponse({"error": "Inicia sesion"}, status_code=401)


def alarm_to_client(row, state=None):
    """Enteros grandes como string (exceden el entero seguro de JS)."""
    out = {
        "id": row["id"],
        "name": row["name"],
        "ip": row["ip"],
        "port": row["port"],
        "player_token": str(row["player_token"]),
        "entity_id": str(row["entity_id"]),
        "check_interval": row["check_interval"],
        "cooldown": row["cooldown"],
        "discord_webhook": row["discord_webhook"],
        "sound": row["sound"] or "",
        "enabled": bool(row["enabled"]),
    }
    if state is not None:
        out["state"] = state
    return out


async def read_json(request: Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


# ================= PAGINAS =================

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    user = current_user(request)
    if user:
        return RedirectResponse("/panel", status_code=302)
    return TEMPLATES.TemplateResponse(request, "landing.html", {})


@app.get("/panel", response_class=HTMLResponse)
async def panel(request: Request):
    user = current_user(request)
    if user is None:
        return RedirectResponse("/", status_code=302)
    return TEMPLATES.TemplateResponse(request, "panel.html", {
        "user": dict(user),
        "admin": is_admin(user),
        "max_alarms": MAX_ALARMS,
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    user = current_user(request)
    if not is_admin(user):
        return RedirectResponse("/", status_code=302)
    return TEMPLATES.TemplateResponse(request, "admin.html", {"user": dict(user)})


# ================= AUTH =================

@app.get("/login")
async def login():
    state = secrets.token_urlsafe(24)
    response = RedirectResponse(steam.login_url(state), status_code=302)
    response.set_cookie(
        OAUTH_STATE_COOKIE, state,
        max_age=600, httponly=True, samesite="lax", secure=SECURE_COOKIES,
    )
    return response


@app.get("/auth/steam/return")
async def steam_return(request: Request):
    # Anti-CSRF: el state que Steam devuelve (firmado dentro de return_to) tiene
    # que coincidir con la cookie que pusimos en /login. Sin esto, un atacante
    # podria loguearte con su cuenta y leer despues los datos que cargues.
    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE, "")
    query_state = request.query_params.get("state", "")
    if not cookie_state or not secrets.compare_digest(cookie_state, query_state):
        return HTMLResponse("Login expirado. <a href='/login'>Reintentar</a>",
                            status_code=400)

    steam_id = await steam.verify(request.query_params)
    if steam_id is None:
        return HTMLResponse("Login fallido. <a href='/'>Volver</a>", status_code=401)

    db.upsert_user(steam_id)
    token = db.create_session(steam_id)

    response = RedirectResponse("/panel", status_code=302)
    response.set_cookie(
        SESSION_COOKIE, token,
        max_age=SESSION_DAYS * 86400,
        httponly=True, samesite="lax", secure=SECURE_COOKIES,
    )
    response.delete_cookie(OAUTH_STATE_COOKIE)
    return response


@app.post("/logout")
async def logout(request: Request):
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    db.delete_session(request.cookies.get(SESSION_COOKIE, ""))
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie(SESSION_COOKIE)
    return response


# ================= API ALARMAS =================

@app.get("/api/alarms")
async def list_alarms(request: Request):
    user = current_user(request)
    if user is None:
        return need_login()
    rows = db.alarms_for_user(user["steam_id"])
    states = manager.snapshot_for([r["id"] for r in rows])
    return {
        "plan_active": bool(user["plan_active"]),
        "max_alarms": MAX_ALARMS,
        "alarms": [alarm_to_client(r, states[r["id"]]) for r in rows],
    }


# Campos que el cliente SI puede mandar. ip/port/player_token/entity_id nunca
# salen del cliente: vienen del pairing (alta) o de lo ya guardado (edicion).
_CLIENT_FIELDS = ("name", "discord_webhook", "check_interval", "cooldown", "sound")


@app.post("/api/alarms")
async def create_alarm(request: Request):
    user = current_user(request)
    if user is None:
        return need_login()
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    # Los datos de conexion salen SOLO del pairing de este usuario, nunca del
    # cliente: no hay forma de cargar una alarma con credenciales a mano.
    session = pairing.pairing_manager.get(user["steam_id"])
    creds, err = pairing.session_credentials(session, user["steam_id"])
    if creds is None:
        return JSONResponse({"error": err}, status_code=400)
    client = await read_json(request)
    data = {k: client.get(k) for k in _CLIENT_FIELDS}
    data.update(creds)
    try:
        row = db.create_alarm(user["steam_id"], data)
    except db.ValidationError as exc:
        return JSONResponse(
            {"error": "Revisa los campos", "errors": exc.errors}, status_code=400
        )
    await manager.sync()
    return {"ok": True, "alarm": alarm_to_client(row)}


@app.put("/api/alarms/{alarm_id}")
async def update_alarm(alarm_id: int, request: Request):
    user = current_user(request)
    if user is None:
        return need_login()
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    existing = db.get_alarm(alarm_id, user["steam_id"])
    if existing is None:
        return JSONResponse({"error": "No existe"}, status_code=404)
    # La edicion toca nombre/webhook/ajustes; las credenciales quedan como
    # estaban (para cambiarlas hay que volver a vincular y crear otra alarma).
    client = await read_json(request)
    data = {k: client.get(k) for k in _CLIENT_FIELDS}
    data.update({
        "ip": existing["ip"], "port": existing["port"],
        "player_token": str(existing["player_token"]),
        "entity_id": str(existing["entity_id"]),
    })
    try:
        row = db.update_alarm(alarm_id, user["steam_id"], data)
    except db.ValidationError as exc:
        return JSONResponse(
            {"error": "Revisa los campos", "errors": exc.errors}, status_code=400
        )
    if row is None:
        return JSONResponse({"error": "No existe"}, status_code=404)
    await manager.sync()
    return {"ok": True, "alarm": alarm_to_client(row)}


@app.post("/api/alarms/{alarm_id}/toggle")
async def toggle_alarm(alarm_id: int, request: Request):
    user = current_user(request)
    if user is None:
        return need_login()
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    row = db.get_alarm(alarm_id, user["steam_id"])
    if row is None:
        return JSONResponse({"error": "No existe"}, status_code=404)
    row = db.set_alarm_enabled(alarm_id, user["steam_id"], not row["enabled"])
    await manager.sync()
    return {"ok": True, "alarm": alarm_to_client(row)}


@app.delete("/api/alarms/{alarm_id}")
async def delete_alarm(alarm_id: int, request: Request):
    user = current_user(request)
    if user is None:
        return need_login()
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    db.delete_alarm(alarm_id, user["steam_id"])
    await manager.sync()
    return {"ok": True}


@app.post("/api/alarms/{alarm_id}/test-webhook")
async def test_webhook(alarm_id: int, request: Request):
    user = current_user(request)
    if user is None:
        return need_login()
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    row = db.get_alarm(alarm_id, user["steam_id"])
    if row is None:
        return JSONResponse({"error": "No existe"}, status_code=404)
    if not row["discord_webhook"]:
        return JSONResponse({"error": "Esta alarma no tiene webhook"}, status_code=400)
    try:
        await send_discord(
            row["discord_webhook"],
            alarm_name=row["name"],
            server=f"{row['ip']}:{row['port']}",
            test=True,
        )
    except Exception:
        # No devolver el exc: puede contener la URL del webhook (secreto).
        return JSONResponse({"error": "Discord rechazo el envio"}, status_code=400)
    return {"ok": True}


@app.post("/api/webhook/test")
async def test_webhook_url(request: Request):
    """Prueba un webhook suelto (URL en el body) antes de que exista la alarma.
    Lo usa el asistente de alta para validar el webhook en el paso de Discord."""
    user = current_user(request)
    if user is None:
        return need_login()
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    data = await read_json(request)
    webhook = str(data.get("webhook", "")).strip()
    if not db.is_discord_webhook(webhook):
        return JSONResponse({"error": "URL de webhook de Discord invalida"},
                            status_code=400)
    name = (str(data.get("name") or "").strip() or "tu alarma")[:60]
    server = (str(data.get("server") or "").strip() or "—")[:100]
    try:
        await send_discord(webhook, alarm_name=name, server=server, test=True)
    except Exception:
        # No devolver el exc: puede contener la URL del webhook (secreto).
        return JSONResponse({"error": "Discord rechazo el envio"}, status_code=400)
    return {"ok": True}


# ================= API PAIRING RUST+ =================

@app.post("/api/pair/start")
async def pair_start(request: Request):
    """Prepara la vinculacion: registra FCM/Expo y devuelve la URL de login de
    Facepunch + un ``link_nonce`` de un solo uso. El panel abre la URL en un
    popup; la extension RustyAlarm Link captura el Token ahi y lo entrega a
    /api/pair/link con ese nonce. Anda en HTTP local igual (no depende de que
    Facepunch redirija a nosotros)."""
    user = current_user(request)
    if user is None:
        return need_login()
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    try:
        session = await pairing.pairing_manager.start(user["steam_id"])
    except pairing.PairingError as exc:
        return JSONResponse({"error": str(exc)}, status_code=503)
    return JSONResponse({
        "ok": True,
        "login_url": pairing.login_url(),
        "link_nonce": session.link_nonce,
    })


@app.post("/api/pair/link")
async def pair_link(request: Request):
    """Entrega del Token desde la extension. NO usa cookie de sesion: la
    autoriza el ``link_nonce`` (capacidad de un solo uso, ligada a una sesion
    de pairing que arranco un usuario logueado). Sin same_origin: la extension
    postea desde el contexto de la pagina de Facepunch. El Token es secreto:
    se usa una vez para registrar el dispositivo y se descarta; nunca se logea."""
    data = await read_json(request)
    nonce = str(data.get("nonce", ""))
    token = str(data.get("token", ""))
    session = pairing.pairing_manager.by_nonce(nonce)
    if session is None:
        return JSONResponse({"error": "Vinculacion no encontrada o vencida"},
                            status_code=404)
    if not token:
        return JSONResponse({"error": "Falta el token"}, status_code=400)
    try:
        await pairing.pairing_manager.activate(session, token)
    except pairing.PairingError as exc:
        return JSONResponse({"error": str(exc)}, status_code=502)
    return {"ok": True}


@app.get("/api/pair/status")
async def pair_status(request: Request):
    user = current_user(request)
    if user is None:
        return need_login()
    session = pairing.pairing_manager.get(user["steam_id"])
    if session is None:
        return {"state": "none"}
    with session.lock:
        server = dict(session.server) if session.server else None
        entity = dict(session.entity) if session.entity else None
        out = {"state": session.state, "error": session.error,
               "server": server, "entity": entity}
    # Si logueo otra cuenta Steam en Facepunch, el playerToken no va a servir
    # para su steam_id: avisar en vez de dejar una alarma que nunca conecta.
    paired_id = (server or entity or {}).get("player_id")
    out["steam_mismatch"] = bool(paired_id and paired_id != user["steam_id"])
    return out


@app.post("/api/pair/cancel")
async def pair_cancel(request: Request):
    user = current_user(request)
    if user is None:
        return need_login()
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    pairing.pairing_manager.cancel(user["steam_id"])
    return {"ok": True}


@app.post("/api/pair/verify")
async def pair_verify(request: Request):
    """Verificacion en vivo antes de crear la alarma: conecta con los datos
    obtenidos y confirma que el Entity ID es una Smart Alarm alcanzable.
    El player_token se usa para conectar y no vuelve nunca al cliente."""
    user = current_user(request)
    if user is None:
        return need_login()
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)

    data = await read_json(request)
    try:
        clean = db.validate_connection(data)   # aplica SSRF (is_blocked_host) + rangos
    except db.ValidationError as exc:
        return JSONResponse(
            {"error": "Revisa los campos", "errors": exc.errors}, status_code=400
        )

    steam_id = user["steam_id"]
    now = time.monotonic()
    if steam_id in _verify_inflight:
        return JSONResponse({"error": "Ya hay una verificacion en curso"},
                            status_code=429)
    if now - _verify_last.get(steam_id, 0.0) < VERIFY_MIN_GAP:
        return JSONResponse({"error": "Espera unos segundos e intenta de nuevo"},
                            status_code=429)
    if len(_verify_inflight) >= VERIFY_MAX_CONCURRENT:
        return JSONResponse({"error": "Hay muchas verificaciones en curso"},
                            status_code=503)

    _verify_inflight.add(steam_id)
    try:
        result = await verify.verify_alarm(
            ip=clean["ip"], port=clean["port"], steam_id=steam_id,
            player_token=clean["player_token"], entity_id=clean["entity_id"],
        )
    finally:
        _verify_inflight.discard(steam_id)
        done = time.monotonic()
        _verify_last[steam_id] = done
        # Podar entradas ya sin efecto (mas viejas que el gap): el dict no
        # crece sin techo con la cantidad de usuarios distintos.
        for sid in [s for s, t in _verify_last.items()
                    if done - t >= VERIFY_MIN_GAP and s != steam_id]:
            _verify_last.pop(sid, None)

    return result


# ================= SONIDOS =================

@app.get("/api/sounds")
async def list_sounds(request: Request):
    if current_user(request) is None:
        return need_login()
    return {"sounds": sounds.catalog(), "default": sounds.default_sound()}


@app.get("/sounds/{file}")
async def get_sound(file: str, request: Request):
    if current_user(request) is None:
        return need_login()
    path = sounds.resolve(file)   # blinda path traversal; None si no existe
    if path is None:
        return JSONResponse({"error": "No existe"}, status_code=404)
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@app.post("/api/admin/sounds")
async def admin_upload_sound(request: Request):
    user = current_user(request)
    if not is_admin(user):
        return JSONResponse({"error": "Solo admin"}, status_code=403)
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    form = await request.form()
    upload = form.get("file")
    if upload is None or not hasattr(upload, "filename") or not upload.filename:
        return JSONResponse({"error": "Falta el archivo"}, status_code=400)
    if Path(upload.filename).suffix.lower() not in sounds.ALLOWED_EXT:
        return JSONResponse({"error": "Formato no permitido (mp3, ogg o wav)"},
                            status_code=400)
    data = await upload.read()
    if len(data) > sounds.MAX_BYTES:
        return JSONResponse({"error": "El archivo supera los 2 MB"}, status_code=400)
    display = str(form.get("name") or "").strip() or Path(upload.filename).stem
    filename = sounds.upload_filename(display, upload.filename)
    try:
        sounds.save_upload(filename, data)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return {"ok": True, "sound": {"file": filename, "builtin": False}}


@app.delete("/api/admin/sounds/{file}")
async def admin_delete_sound(file: str, request: Request):
    user = current_user(request)
    if not is_admin(user):
        return JSONResponse({"error": "Solo admin"}, status_code=403)
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    if not sounds.delete_upload(file):   # solo sonidos subidos, nunca built-in
        return JSONResponse({"error": "No existe o es un sonido de fabrica"},
                            status_code=404)
    return {"ok": True}


# ================= API ADMIN =================

@app.get("/api/admin/users")
async def admin_users(request: Request):
    user = current_user(request)
    if not is_admin(user):
        return JSONResponse({"error": "Solo admin"}, status_code=403)
    rows = db.all_users()
    return {"users": [dict(r) for r in rows]}


@app.post("/api/admin/users/{steam_id}/toggle")
async def admin_toggle(steam_id: str, request: Request):
    user = current_user(request)
    if not is_admin(user):
        return JSONResponse({"error": "Solo admin"}, status_code=403)
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    target = db.get_user(steam_id)
    if target is None:
        return JSONResponse({"error": "No existe"}, status_code=404)
    db.set_plan_active(steam_id, not target["plan_active"])
    await manager.sync()
    return {"ok": True}
