"""Rutas FastAPI: landing, login Steam, panel de alarmas y admin.

Arranque: python -m saas
"""

import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import db, steam
from .config import ADMIN_STEAM_ID, BASE_URL, MAX_ALARMS, SESSION_COOKIE, SESSION_DAYS
from .monitor import manager
from .notify import send_discord

OAUTH_STATE_COOKIE = "rustalarm_oauth_state"

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


@app.post("/api/alarms")
async def create_alarm(request: Request):
    user = current_user(request)
    if user is None:
        return need_login()
    if not same_origin(request):
        return JSONResponse({"error": "Origen invalido"}, status_code=403)
    data = await read_json(request)
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
    data = await read_json(request)
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
