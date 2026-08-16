"""Vinculacion nativa con Rust+ (pairing del companion).

Espeja el flujo de rustplus.js / rustCli:

 1. ``start()`` registra credenciales FCM propias (Firebase Installations +
    GCM checkin/register3, via ``push_receiver.AndroidFCM``) y pide el
    ``ExponentPushToken`` a Expo. Devuelve la URL de login de Facepunch con
    ``returnUrl`` apuntando a ``/pair/callback``.
 2. El usuario loguea con Steam en companion-rust.facepunch.com; Facepunch
    redirige a ``/pair/callback?token=<AuthToken>``.
 3. ``activate()`` registra nuestro token Expo como "dispositivo" de la cuenta
    (POST /api/push/register) y abre un listener MCS (mtalk.google.com:5228)
    en un thread daemon.
 4. El jugador parea el servidor / la alarma en el juego; la notificacion FCM
    trae un JSON en ``app_data["body"]`` que el wizard lee por polling.

Todo el estado vive en memoria. El AuthToken de Facepunch es un secreto:
NUNCA va a la base, a los logs ni al cliente.
"""

import asyncio
import json
import logging
import secrets
import socket
import ssl
import threading
import time
import uuid
from urllib.parse import quote

import httpx
from push_receiver import PushReceiver
from push_receiver.android_fcm_register import AndroidFCM
from push_receiver.mcs import Close, DataMessageStanza, HeartbeatPing

log = logging.getLogger("rustalarm.pairing")

# Constantes publicas de la app companion oficial (com.facepunch.rust.companion).
# Son las mismas que usa rustplus.js/rustCli; no son secretos.
FCM_API_KEY = "AIzaSyB5y2y-Tzqb4-I4Qnlsh_9naYv_TD8pCvY"
FCM_PROJECT_ID = "rust-companion-app"
GCM_SENDER_ID = "976529667804"
GMS_APP_ID = "1:976529667804:android:d6f1ddeb4403b338fea619"
ANDROID_PACKAGE = "com.facepunch.rust.companion"
ANDROID_CERT = "E28D05345FB78A7A1A63D70F4A302DBF426CA5AD"
EXPO_PROJECT_ID = "49451aca-a822-41e6-ad59-955718d0ff9c"

COMPANION_URL = "https://companion-rust.facepunch.com"
EXPO_TOKEN_URL = "https://exp.host/--/api/v2/push/getExpoPushToken"

WAIT_LOGIN_TTL = 5 * 60      # seg sin completar el login de Facepunch
LISTEN_TTL = 10 * 60         # seg de escucha de notificaciones
MAX_SESSIONS = 8             # listeners MCS concurrentes en todo el proceso


class PairingError(Exception):
    """Fallo de un paso del pairing, con mensaje apto para el usuario."""


MCS_HOST = "mtalk.google.com"
MCS_PORTS = (5228, 443)  # 5228 es el clasico; muchas redes lo filtran -> 443


def _open_mcs_socket(receiver: PushReceiver) -> None:
    """Reemplazo de PushReceiver.__open: con timeout de conexion y fallback de
    puerto (el original bloquea sin timeout en 5228)."""
    context = ssl.create_default_context()
    last_error = None
    for port in MCS_PORTS:
        try:
            sock = socket.create_connection((MCS_HOST, port), timeout=10)
            wrapped = context.wrap_socket(sock, server_hostname=MCS_HOST)
            wrapped.settimeout(None)  # el select del receiver marca los reads
            receiver.socket = wrapped
            return
        except OSError as exc:
            last_error = exc
    raise last_error


class PairingSession:
    """Una vinculacion en curso para un usuario. Estado bajo ``self.lock``."""

    def __init__(self, steam_id: str):
        self.steam_id = steam_id
        self.state = "registering"   # registering|waiting_login|listening|expired|error
        self.csrf = secrets.token_urlsafe(16)
        # Capacidad de un solo uso que autoriza a la extension a entregar el
        # Token sin cookie nuestra. Se consume al vincular.
        self.link_nonce = secrets.token_urlsafe(24)
        self.created = time.monotonic()
        self.lock = threading.Lock()
        self.fcm_credentials = None
        self.expo_token = None
        self.server = None           # ultimo pairing type=server
        self.entity = None           # ultimo pairing type=entity
        self.error = None
        self.stop_event = threading.Event()
        self._receiver = None
        self._thread = None

    # ---- registro FCM + Expo (bloqueante; llamar via asyncio.to_thread) ----

    def register_push(self) -> None:
        creds = AndroidFCM.register(
            api_key=FCM_API_KEY,
            project_id=FCM_PROJECT_ID,
            gcm_sender_id=GCM_SENDER_ID,
            gms_app_id=GMS_APP_ID,
            android_package_name=ANDROID_PACKAGE,
            android_package_cert=ANDROID_CERT,
        )
        if not creds or not creds.get("fcm", {}).get("token"):
            raise PairingError("No se pudo registrar el dispositivo (FCM)")

        response = httpx.post(EXPO_TOKEN_URL, json={
            "type": "fcm",
            "deviceId": str(uuid.uuid4()),
            "development": False,
            "appId": ANDROID_PACKAGE,
            "deviceToken": creds["fcm"]["token"],
            "projectId": EXPO_PROJECT_ID,
        }, timeout=15)
        response.raise_for_status()
        expo_token = response.json().get("data", {}).get("expoPushToken")
        if not expo_token:
            raise PairingError("Expo no devolvio un push token")

        with self.lock:
            self.fcm_credentials = creds
            self.expo_token = expo_token
            self.state = "waiting_login"

    # ---- escucha MCS ----

    def start_listening(self) -> None:
        self._thread = threading.Thread(
            target=self._listen, name=f"pairing-{self.steam_id}", daemon=True)
        self._thread.start()
        with self.lock:
            self.state = "listening"
            self.created = time.monotonic()  # el TTL de escucha arranca aca

    def _listen(self) -> None:
        """Loop MCS cortable. Usa los privados de PushReceiver (version pineada
        via rustplus -> rustPlusPushReceiver==0.6.1): su listen() oficial
        reconecta para siempre y no se puede frenar."""
        try:
            receiver = PushReceiver(credentials=self.fcm_credentials)
            receiver.checkin_thread = threading.Timer(0, lambda: None)  # __del__
            # Timeout corto por instancia (pisa el de clase, 1h): el loop se
            # despierta seguido y un stop() corta en segundos, no en horas.
            receiver.READ_TIMEOUT_SECS = 5
            # El atributo de instancia con nombre mangleado pisa al metodo de
            # clase: __login llama a self._PushReceiver__open y encuentra este.
            receiver._PushReceiver__open = lambda: _open_mcs_socket(receiver)
            self._receiver = receiver
            login = getattr(receiver, "_PushReceiver__login")
            recv = getattr(receiver, "_PushReceiver__recv")
            ping = getattr(receiver, "_PushReceiver__handle_ping")
            login()
            relogins = 0
            fails = 0
            while not self.stop_event.is_set():
                started = time.monotonic()
                packet = recv()
                if self.stop_event.is_set():
                    break
                if packet is None:
                    # recv() devuelve None tanto por timeout del select (silencio
                    # normal) como por error de socket. Los distingue el tiempo:
                    # un None instantaneo es un socket roto.
                    if time.monotonic() - started < 1.0:
                        fails += 1
                        if fails >= 3:
                            relogins += 1
                            if relogins > 3:
                                raise PairingError("Se corto la conexion con FCM")
                            fails = 0
                            time.sleep(2)
                            login()
                        else:
                            time.sleep(0.5)
                    continue
                fails = 0
                if isinstance(packet, DataMessageStanza):
                    self._on_message(packet)
                elif isinstance(packet, HeartbeatPing):
                    ping(packet)
                elif isinstance(packet, Close):
                    relogins += 1
                    if relogins > 3:
                        raise PairingError("Se corto la conexion con FCM")
                    time.sleep(2)
                    login()
        except Exception:
            log.exception("Listener de pairing caido (steam_id=%s)", self.steam_id)
            with self.lock:
                if self.state == "listening":
                    self.state = "error"
                    self.error = "Se corto la escucha; reintenta la vinculacion"
        finally:
            self._close_socket()

    def _on_message(self, packet) -> None:
        data = {item.key: item.value for item in packet.app_data}
        try:
            body = json.loads(data.get("body", ""))
        except (TypeError, ValueError):
            return
        kind = body.get("type")
        payload = {
            "name": str(body.get("name") or ""),
            "ip": str(body.get("ip") or ""),
            "port": str(body.get("port") or ""),
            "player_id": str(body.get("playerId") or ""),
            "player_token": str(body.get("playerToken") or ""),
        }
        with self.lock:
            if kind == "server":
                self.server = payload
            elif kind == "entity":
                payload["entity_id"] = str(body.get("entityId") or "")
                payload["entity_type"] = str(body.get("entityType") or "")
                payload["entity_name"] = str(body.get("entityName") or "")
                self.entity = payload

    # ---- cierre ----

    def stop(self) -> None:
        self.stop_event.set()
        self._close_socket()

    def _close_socket(self) -> None:
        receiver = self._receiver
        if receiver is not None:
            try:
                getattr(receiver, "_PushReceiver__close_socket")()
            except Exception:
                pass

    def ttl_expired(self) -> bool:
        limit = LISTEN_TTL if self.state == "listening" else WAIT_LOGIN_TTL
        return time.monotonic() - self.created > limit


class PairingManager:
    """Sesiones de pairing por steam_id. Vive en el unico proceso/loop."""

    def __init__(self):
        self.sessions: dict[str, PairingSession] = {}
        self._lock = threading.Lock()

    def get(self, steam_id: str):
        return self.sessions.get(steam_id)

    def by_nonce(self, nonce: str):
        """Sesion que espera login y cuyo link_nonce coincide (comparacion en
        tiempo constante). None si no hay ninguna."""
        if not nonce:
            return None
        for session in self.sessions.values():
            if (session.state == "waiting_login"
                    and secrets.compare_digest(session.link_nonce, nonce)):
                return session
        return None

    async def start(self, steam_id: str) -> PairingSession:
        with self._lock:
            self._sweep_locked()
            old = self.sessions.pop(steam_id, None)
            active = sum(1 for s in self.sessions.values()
                         if s.state in ("registering", "waiting_login", "listening"))
            if active >= MAX_SESSIONS:
                raise PairingError(
                    "Hay muchas vinculaciones en curso; proba en unos minutos")
            session = PairingSession(steam_id)
            self.sessions[steam_id] = session
        if old is not None:
            old.stop()
        try:
            await asyncio.to_thread(session.register_push)
        except Exception as exc:
            with self._lock:
                # Solo sacar la sesion si sigue siendo esta (pudo re-arrancar).
                if self.sessions.get(steam_id) is session:
                    self.sessions.pop(steam_id)
            if isinstance(exc, PairingError):
                raise
            log.warning("Registro FCM/Expo fallo: %s", type(exc).__name__)
            raise PairingError("No se pudo preparar la vinculacion; reintenta")
        asyncio.get_running_loop().create_task(self._expire(session))
        return session

    async def activate(self, session: PairingSession, auth_token: str) -> None:
        """Registra el dispositivo en la cuenta Facepunch y arranca la escucha.
        ``auth_token`` no se persiste: se usa y se descarta."""
        # Consumir el nonce: el link es de un solo uso.
        session.link_nonce = ""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(f"{COMPANION_URL}/api/push/register", json={
                    "AuthToken": auth_token,
                    "DeviceId": "rustyalarm",
                    "PushKind": 3,
                    "PushToken": session.expo_token,
                })
        except Exception:
            # Ojo: no loguear el detalle, la request lleva el AuthToken.
            with session.lock:
                session.state = "error"
                session.error = "No se pudo llegar a Facepunch; reintenta"
            raise PairingError(session.error)
        if response.status_code != 200:
            with session.lock:
                session.state = "error"
                session.error = "Facepunch rechazo el registro; reintenta"
            raise PairingError(session.error)
        session.start_listening()

    async def _expire(self, session: PairingSession) -> None:
        # Doble espera: TTL de login y despues (si se activo) TTL de escucha.
        await asyncio.sleep(WAIT_LOGIN_TTL)
        if session.state == "listening":
            remaining = LISTEN_TTL - (time.monotonic() - session.created)
            if remaining > 0:
                await asyncio.sleep(remaining)
        with session.lock:
            if session.state in ("registering", "waiting_login", "listening"):
                session.state = "expired"
        session.stop()

    def cancel(self, steam_id: str) -> None:
        with self._lock:
            session = self.sessions.pop(steam_id, None)
        if session is not None:
            session.stop()

    def _sweep_locked(self) -> None:
        for sid in [sid for sid, s in self.sessions.items()
                    if s.state in ("expired", "error") or s.ttl_expired()]:
            self.sessions.pop(sid).stop()


def login_url() -> str:
    # Sin returnUrl: la extension captura el Token via ReactNativeWebView.
    # postMessage en la propia pagina de Facepunch, no por redirect.
    return f"{COMPANION_URL}/login"


pairing_manager = PairingManager()
