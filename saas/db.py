"""SQLite: usuarios, sesiones y alarmas. Sincronico con lock global.

A esta escala (decenas de usuarios) sqlite3 en WAL con un lock alcanza de
sobra. Las corutinas del monitor escriben via asyncio.to_thread para no
bloquear el event loop.
"""

import hashlib
import ipaddress
import math
import secrets
import sqlite3
import threading
import time

from .config import DB_PATH, MAX_ALARMS, SESSION_DAYS

_lock = threading.RLock()
_conn = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    steam_id      TEXT PRIMARY KEY,
    display_name  TEXT NOT NULL DEFAULT '',
    plan          TEXT NOT NULL DEFAULT 'beta',
    plan_active   INTEGER NOT NULL DEFAULT 1,
    is_admin      INTEGER NOT NULL DEFAULT 0,
    created_at    REAL NOT NULL,
    last_login_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    steam_id   TEXT NOT NULL REFERENCES users(steam_id) ON DELETE CASCADE,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS alarms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    steam_id        TEXT NOT NULL REFERENCES users(steam_id) ON DELETE CASCADE,
    name            TEXT NOT NULL DEFAULT 'Mi alarma',
    ip              TEXT NOT NULL,
    port            TEXT NOT NULL,
    player_token    INTEGER NOT NULL,
    entity_id       INTEGER NOT NULL,
    check_interval  REAL NOT NULL DEFAULT 3,
    cooldown        REAL NOT NULL DEFAULT 30,
    discord_webhook TEXT NOT NULL DEFAULT '',
    enabled         INTEGER NOT NULL DEFAULT 1,
    created_at      REAL NOT NULL,
    updated_at      REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alarms_steam ON alarms(steam_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
"""


def connect():
    global _conn
    with _lock:
        if _conn is None:
            _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode=WAL")
            _conn.execute("PRAGMA foreign_keys=ON")
            _conn.executescript(SCHEMA)
            _conn.commit()
        return _conn


def _run(sql, params=(), *, fetch=None):
    conn = connect()
    with _lock:
        cur = conn.execute(sql, params)
        if fetch == "one":
            result = cur.fetchone()
        elif fetch == "all":
            result = cur.fetchall()
        else:
            result = cur
        conn.commit()
        return result


# ================= USUARIOS =================

def upsert_user(steam_id: str, display_name: str = ""):
    now = time.time()
    with _lock:
        row = _run("SELECT * FROM users WHERE steam_id=?", (steam_id,), fetch="one")
        if row is None:
            _run(
                "INSERT INTO users (steam_id, display_name, created_at, last_login_at)"
                " VALUES (?,?,?,?)",
                (steam_id, display_name, now, now),
            )
        else:
            _run(
                "UPDATE users SET last_login_at=?, display_name=CASE WHEN ?=''"
                " THEN display_name ELSE ? END WHERE steam_id=?",
                (now, display_name, display_name, steam_id),
            )
        return get_user(steam_id)


def get_user(steam_id: str):
    return _run("SELECT * FROM users WHERE steam_id=?", (steam_id,), fetch="one")


def all_users():
    return _run(
        "SELECT u.*, COUNT(a.id) AS alarm_count FROM users u"
        " LEFT JOIN alarms a ON a.steam_id = u.steam_id"
        " GROUP BY u.steam_id ORDER BY u.created_at",
        fetch="all",
    )


def set_plan_active(steam_id: str, active: bool):
    _run("UPDATE users SET plan_active=? WHERE steam_id=?",
         (1 if active else 0, steam_id))


# ================= SESIONES =================

def _hash_token(token: str) -> str:
    """La cookie lleva el token en claro; la base guarda solo su hash, asi un
    volcado de la DB no da sesiones usables."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(steam_id: str) -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    _run(
        "INSERT INTO sessions (token, steam_id, created_at, expires_at) VALUES (?,?,?,?)",
        (_hash_token(token), steam_id, now, now + SESSION_DAYS * 86400),
    )
    # higiene: borrar sesiones vencidas de paso
    _run("DELETE FROM sessions WHERE expires_at < ?", (now,))
    return token


def user_by_session(token: str):
    if not token:
        return None
    row = _run(
        "SELECT u.* FROM sessions s JOIN users u ON u.steam_id = s.steam_id"
        " WHERE s.token=? AND s.expires_at > ?",
        (_hash_token(token), time.time()),
        fetch="one",
    )
    return row


def delete_session(token: str):
    _run("DELETE FROM sessions WHERE token=?", (_hash_token(token),))


# ================= ALARMAS =================

class ValidationError(Exception):
    def __init__(self, errors):
        super().__init__("Datos invalidos")
        self.errors = errors


_WEBHOOK_PREFIXES = (
    "https://discord.com/api/webhooks/",
    "https://discordapp.com/api/webhooks/",
    "https://canary.discord.com/api/webhooks/",
    "https://ptb.discord.com/api/webhooks/",
)


def is_discord_webhook(url: str) -> bool:
    return bool(url) and url.startswith(_WEBHOOK_PREFIXES)


def _looks_like_numeric_host(h: str) -> bool:
    """Formas numericas empaquetadas de una IP que ipaddress.ip_address() NO
    parsea pero glibc getaddrinfo SI resuelve (a loopback/privadas): decimal
    suelto (2130706433 = 127.0.0.1), hex (0x7f000001), octal por segmento
    (0177.0.0.1). Un hostname real siempre tiene alguna letra en su TLD."""
    if h.startswith(("0x", "0X")):
        return True
    labels = [lbl for lbl in h.split(".") if lbl]
    if labels and all(lbl.isdigit() for lbl in labels):
        return True  # solo digitos y puntos: no es un hostname, es una IP disfrazada
    for lbl in labels:
        if len(lbl) > 1 and lbl[0] == "0" and lbl.isdigit():
            return True  # segmento con cero a la izquierda: octal
    return False


def is_blocked_host(host: str) -> bool:
    """SSRF: el monitor abre un socket al host que ponga el usuario. Los
    servidores de Rust son publicos, asi que bloqueamos privadas/loopback/
    link-local/metadata para que nadie apunte a la red interna del VPS.

    Ojo: esto NO resuelve DNS, asi que un hostname publico cuyo registro A
    apunte a una IP interna igual pasa. La verificacion en vivo (verify.py)
    resuelve y re-chequea cada IP antes de conectar; el monitor (crear alarma)
    conserva ese hueco de rebind -> hardening pendiente (ver docs)."""
    h = host.strip().lower().rstrip(".")
    if h in ("", "localhost", "0.0.0.0", "::", "ip6-localhost"):
        return True
    try:
        addr = ipaddress.ip_address(h)
    except ValueError:
        # Es un hostname (o una IP en notacion rara). Cortamos las numericas
        # empaquetadas y los sufijos internos obvios.
        return (_looks_like_numeric_host(h)
                or h.endswith(".local") or h.endswith(".internal"))
    return (addr.is_private or addr.is_loopback or addr.is_link_local
            or addr.is_reserved or addr.is_unspecified or addr.is_multicast)


def _validate_connection_fields(data: dict, errors: dict, clean: dict) -> None:
    """Valida ip/port/player_token/entity_id (lo que hace falta para conectar
    al Companion Server). Muta ``errors``/``clean``. Lo comparten el alta de
    alarma y la verificacion en vivo, asi ambas aplican identicas reglas de
    SSRF y de rango."""
    ip = str(data.get("ip", "")).strip()
    if not ip:
        errors["ip"] = "Requerido"
    elif len(ip) > 253:
        errors["ip"] = "Demasiado largo"
    # Solo host/IP validos: letras, digitos, punto y guion. Corta cualquier
    # payload de HTML/JS antes de que llegue a guardarse.
    elif any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
             for c in ip):
        errors["ip"] = "IP o dominio invalido"
    elif is_blocked_host(ip):
        errors["ip"] = "IP privada o local no permitida"
    clean["ip"] = ip

    port = str(data.get("port", "")).strip()
    # isascii(): "٤" pasa isdigit() pero no es un puerto valido para el socket.
    if not (port.isascii() and port.isdigit()) or not (1 <= int(port) <= 65535):
        errors["port"] = "Numero entre 1 y 65535"
    clean["port"] = port

    for field, label, allow_negative in (
        ("player_token", "Player token", True),
        ("entity_id", "Entity ID", False),
    ):
        raw = str(data.get(field, "")).strip()
        try:
            value = int(raw)
            if not allow_negative and value <= 0:
                raise ValueError
            # Rust+ usa enteros de 32 bits con signo; fuera de rango es basura.
            if not (-2_147_483_648 <= value <= 2_147_483_647):
                raise ValueError
            clean[field] = value
        except ValueError:
            errors[field] = f"{label} debe ser un numero entero" + (
                "" if allow_negative else " mayor que 0"
            )


def validate_connection(data: dict) -> dict:
    """Valida solo los datos de conexion (para la verificacion en vivo)."""
    errors, clean = {}, {}
    _validate_connection_fields(data, errors, clean)
    if errors:
        raise ValidationError(errors)
    return clean


def validate_alarm(data: dict) -> dict:
    """Normaliza el payload del formulario. Todos los errores juntos."""
    errors = {}
    clean = {}

    name = str(data.get("name", "")).strip() or "Mi alarma"
    clean["name"] = name[:60]

    _validate_connection_fields(data, errors, clean)

    for field, minimum, maximum in (
        ("check_interval", 2, 3600),
        ("cooldown", 0, 86400),
    ):
        raw = str(data.get(field, "")).strip()
        try:
            value = float(raw)
            if not math.isfinite(value) or not (minimum <= value <= maximum):
                raise ValueError
            clean[field] = int(value) if value == int(value) else value
        except ValueError:
            errors[field] = f"Numero entre {minimum} y {maximum}"

    webhook = str(data.get("discord_webhook", "")).strip()
    if webhook and not webhook.startswith(_WEBHOOK_PREFIXES):
        errors["discord_webhook"] = "Debe ser una URL de webhook de Discord"
    clean["discord_webhook"] = webhook

    if errors:
        raise ValidationError(errors)
    return clean


def alarms_for_user(steam_id: str):
    return _run(
        "SELECT * FROM alarms WHERE steam_id=? ORDER BY id", (steam_id,), fetch="all"
    )


def get_alarm(alarm_id: int, steam_id: str = None):
    """Con steam_id filtra por dueno: nunca devolver alarmas ajenas."""
    if steam_id is None:
        return _run("SELECT * FROM alarms WHERE id=?", (alarm_id,), fetch="one")
    return _run(
        "SELECT * FROM alarms WHERE id=? AND steam_id=?",
        (alarm_id, steam_id), fetch="one",
    )


def create_alarm(steam_id: str, data: dict):
    clean = validate_alarm(data)
    with _lock:
        count = _run(
            "SELECT COUNT(*) AS n FROM alarms WHERE steam_id=?",
            (steam_id,), fetch="one",
        )["n"]
        if count >= MAX_ALARMS:
            raise ValidationError({"_": f"Maximo {MAX_ALARMS} alarmas por cuenta"})
        now = time.time()
        cur = _run(
            "INSERT INTO alarms (steam_id, name, ip, port, player_token, entity_id,"
            " check_interval, cooldown, discord_webhook, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (steam_id, clean["name"], clean["ip"], clean["port"],
             clean["player_token"], clean["entity_id"], clean["check_interval"],
             clean["cooldown"], clean["discord_webhook"], now, now),
        )
        return get_alarm(cur.lastrowid)


def update_alarm(alarm_id: int, steam_id: str, data: dict):
    if get_alarm(alarm_id, steam_id) is None:
        return None
    clean = validate_alarm(data)
    _run(
        "UPDATE alarms SET name=?, ip=?, port=?, player_token=?, entity_id=?,"
        " check_interval=?, cooldown=?, discord_webhook=?, updated_at=?"
        " WHERE id=? AND steam_id=?",
        (clean["name"], clean["ip"], clean["port"], clean["player_token"],
         clean["entity_id"], clean["check_interval"], clean["cooldown"],
         clean["discord_webhook"], time.time(), alarm_id, steam_id),
    )
    return get_alarm(alarm_id)


def set_alarm_enabled(alarm_id: int, steam_id: str, enabled: bool):
    _run(
        "UPDATE alarms SET enabled=?, updated_at=? WHERE id=? AND steam_id=?",
        (1 if enabled else 0, time.time(), alarm_id, steam_id),
    )
    return get_alarm(alarm_id, steam_id)


def delete_alarm(alarm_id: int, steam_id: str):
    _run("DELETE FROM alarms WHERE id=? AND steam_id=?", (alarm_id, steam_id))


def active_alarms():
    """Alarmas habilitadas de usuarios con plan activo: lo que hay que monitorear."""
    return _run(
        "SELECT a.* FROM alarms a JOIN users u ON u.steam_id = a.steam_id"
        " WHERE a.enabled=1 AND u.plan_active=1 ORDER BY a.id",
        fetch="all",
    )
