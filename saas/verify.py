"""Verificacion en vivo de credenciales Rust+ y de una Smart Alarm.

Una unica conexion efimera al Companion Server: confirma que el server
responde, que las credenciales autentican y que el Entity ID apunta a una
Smart Alarm (no un Switch ni un Storage Monitor) — todo ANTES de que el usuario
cree la alarma. Ataja el caso `not_found` (el Entity ID cambia con cada wipe)
que, si no, recien aparece como warnings en el monitor una vez creada.

Aislado del monitor a proposito: esto es un chequeo de un tiro, no una corutina
de larga vida. Si Rust+/rustplus cambia, se toca solo este adapter.
"""

import asyncio
import logging
import socket as _socket

from rustplus import RustSocket, ServerDetails
from rustplus.structs.rust_error import RustError

from . import db
from .monitor import quiet_rustplus_logger

log = logging.getLogger("rustalarm.verify")

RESOLVE_TIMEOUT = 8

# AppEntityType del proto de rustplus: Switch=1, Alarm=2, StorageMonitor=3.
SMART_ALARM_TYPE = 2
ENTITY_TYPE_NAME = {1: "Smart Switch", 2: "Smart Alarm", 3: "Storage Monitor"}

CONNECT_TIMEOUT = 12
ENTITY_TIMEOUT = 12

# Taxonomia de errores (brief §26) -> mensaje para el usuario (es).
MESSAGES = {
    "RUST_SERVER_UNREACHABLE":
        "No conecta al servidor. Revisa IP y puerto Rust+, o el server esta caido.",
    "RUST_AUTH_REJECTED":
        "El servidor rechazo las credenciales. Revisa el player token.",
    "RUST_ENTITY_NOT_FOUND":
        "El Entity ID no existe en este servidor. Ojo: cambia con cada wipe.",
    "RUST_ENTITY_UNSUPPORTED":
        "Ese dispositivo no es una Smart Alarm.",
    "RUST_NO_READ":
        "No pudimos leer la alarma. Revisa el player token (cambia con cada"
        " wipe) y que el Entity ID sea el correcto.",
    "RUST_PROTOCOL_ERROR":
        "Error hablando con Rust+. Proba de nuevo en un momento.",
}


async def _safe_resolve(host: str, port) -> str | None:
    """Resuelve el host y verifica que NINGUNA IP resuelta sea interna: cierra
    el hueco SSRF de is_blocked_host (que no resuelve DNS) y la notacion
    numerica que glibc expande a loopback. Devuelve una IP literal fijada para
    conectar (sin rebind entre chequeo y uso), o None si algo resuelve a un
    rango bloqueado o no resuelve."""
    loop = asyncio.get_running_loop()
    try:
        infos = await asyncio.wait_for(
            loop.getaddrinfo(host, int(port), type=_socket.SOCK_STREAM),
            RESOLVE_TIMEOUT)
    except (OSError, ValueError, asyncio.TimeoutError):
        return None
    pinned = None
    for info in infos:
        ip = info[4][0]
        if db.is_blocked_host(ip):
            return None
        if pinned is None:
            pinned = ip
    return pinned


def _fail(code: str, detail: str = "") -> dict:
    out = {"ok": False, "code": code, "message": MESSAGES.get(code, MESSAGES["RUST_PROTOCOL_ERROR"])}
    if detail:
        out["detail"] = detail
    return out


async def verify_alarm(ip: str, port, steam_id: str, player_token: int,
                       entity_id: int) -> dict:
    """Conecta una vez y chequea la alarma. Nunca lanza: devuelve un dict con
    ``ok`` y, si falla, ``code``/``message`` de la taxonomia. Los valores
    (ip/port/player_token/entity_id) YA vienen validados por db.validate_*."""
    # Resolver y re-chequear antes de conectar (SSRF): is_blocked_host no
    # resuelve DNS. Conectamos a la IP fijada para que no haya rebind.
    pinned = await _safe_resolve(ip, port)
    if pinned is None:
        return _fail("RUST_SERVER_UNREACHABLE")

    details = ServerDetails(pinned, port, int(steam_id), player_token)
    socket = RustSocket(details)
    quiet_rustplus_logger()  # rustplus filtra un handler nuevo en cada RustSocket()

    try:
        # connect() devuelve False (no lanza) si el server no responde; y puede
        # colgar en hosts raros, por eso el wait_for.
        try:
            connected = await asyncio.wait_for(socket.connect(), CONNECT_TIMEOUT)
        except asyncio.TimeoutError:
            return _fail("RUST_SERVER_UNREACHABLE")
        except asyncio.CancelledError:
            raise
        except Exception:
            return _fail("RUST_SERVER_UNREACHABLE")
        if not connected:
            return _fail("RUST_SERVER_UNREACHABLE")

        try:
            entity = await asyncio.wait_for(
                socket.get_entity_info(entity_id), ENTITY_TIMEOUT)
        except asyncio.TimeoutError:
            return _fail("RUST_PROTOCOL_ERROR")
        except asyncio.CancelledError:
            raise
        except Exception:
            return _fail("RUST_PROTOCOL_ERROR")

        # get_entity_info devuelve un RustError, NO lo lanza. Solo afirmamos
        # "el entity no existe" cuando Rust lo dice literal (not_found); para
        # cualquier otro motivo (incluida la falta de respuesta por un player
        # token de otro wipe) damos un mensaje neutral que no culpa al Entity ID.
        if isinstance(entity, RustError):
            reason = (getattr(entity, "reason", "") or "").lower()
            if "not_found" in reason or "not found" in reason:
                return _fail("RUST_ENTITY_NOT_FOUND", reason)
            return _fail("RUST_NO_READ", reason)

        etype = getattr(entity, "type", None)
        if etype != SMART_ALARM_TYPE:
            found = ENTITY_TYPE_NAME.get(etype, f"tipo {etype}")
            return _fail("RUST_ENTITY_UNSUPPORTED", found)

        return {"ok": True, "entity_type": etype, "value": bool(entity.value)}
    finally:
        try:
            await socket.disconnect()
        except Exception:
            pass
