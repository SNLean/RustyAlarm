"""Monitoreo multiusuario: una corutina por alarma habilitada, todas en el
event loop de uvicorn.

`Manager.sync()` reconcilia la tabla `alarms` contra las corutinas vivas:
arranca las nuevas, corta las borradas/deshabilitadas y reinicia las que
cambiaron de datos (updated_at distinto). Se llama tras cada CRUD y ademas
cada SYNC_INTERVAL segundos por si algo cambio por fuera (admin).
"""

import asyncio
import logging
import time
from collections import deque

from rustplus import RustSocket, ServerDetails
from rustplus.structs.rust_error import RustError

from . import db
from .notify import send_discord

SYNC_INTERVAL = 30
RETRY_BASE = 15          # primer reintento de conexion
RETRY_MAX = 300          # tope de backoff
MIN_INTERVAL = 2         # piso duro de sondeo, no negociable por el usuario
RECONNECT_AFTER = 8      # respuestas fallidas seguidas antes de reconectar


def quiet_rustplus_logger():
    """rustplus 6.0.9 agrega un StreamHandler nuevo y pone DEBUG en CADA
    RustSocket(). Creamos un socket por intento de conexion, asi que sin esto
    los handlers se acumulan sin techo (fuga de memoria + log duplicado).
    Se llama despues de construir cada socket: deja el logger en cero handlers.
    """
    lg = logging.getLogger("rustplus.py")
    lg.handlers.clear()
    lg.propagate = False
    lg.setLevel(logging.CRITICAL)


quiet_rustplus_logger()


class AlarmRunner:
    """Estado vivo + corutina de una alarma."""

    def __init__(self, row):
        self.row = dict(row)
        self.updated_at = row["updated_at"]
        self.task = None

        self.status = "starting"     # starting | running | retrying | error | stopped
        self.detail = ""
        self.alarm_on = False
        self.last_check = None
        self.last_trigger = None
        self.trigger_count = 0
        self.logs = deque(maxlen=100)
        self._seq = 0

    def log(self, level, message):
        self._seq += 1
        self.logs.append({
            "seq": self._seq, "ts": time.time(),
            "level": level, "message": str(message),
        })

    def snapshot(self):
        return {
            "status": self.status,
            "detail": self.detail,
            "alarm_on": self.alarm_on,
            "last_check": self.last_check,
            "last_trigger": self.last_trigger,
            "trigger_count": self.trigger_count,
            "logs": list(self.logs),
        }

    async def run(self):
        backoff = RETRY_BASE
        while True:
            try:
                healthy = await self._session()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                healthy = False
                self.log("error", f"Fallo inesperado: {exc}")

            # backoff se resetea solo si la sesion llego a leer bien alguna vez.
            # Config permanentemente rota (entity que no existe) => nunca healthy
            # => el backoff crece hasta RETRY_MAX en vez de reconectar sin parar.
            if healthy:
                backoff = RETRY_BASE

            self.status = "retrying"
            self.detail = f"Reintentando en {backoff}s"
            self.log("warn", f"Desconectado. Reintento en {backoff}s")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, RETRY_MAX)

    async def _session(self) -> bool:
        """Una conexion completa. Devuelve True si llego a leer la alarma al
        menos una vez (sesion sana); False si nunca funciono."""
        row = self.row
        details = ServerDetails(
            row["ip"], row["port"], int(row["steam_id"]), row["player_token"]
        )
        socket = RustSocket(details)
        quiet_rustplus_logger()

        self.status = "starting"
        self.detail = "Conectando..."
        # connect() devuelve False en vez de lanzar cuando el server no responde.
        try:
            connected = await socket.connect()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.status = "error"
            self.detail = f"No conecta: {exc}"
            self.log("error", f"No se pudo conectar: {exc}")
            return False
        if not connected:
            self.status = "error"
            self.detail = "No conecta (server caido o IP/puerto mal)"
            self.log("error", "No se pudo conectar: revisa IP y puerto Rust+")
            return False

        self.status = "running"
        self.detail = "Conectado"
        self.log("ok", "Conectado a Rust+")

        interval = max(float(row["check_interval"]), MIN_INTERVAL)
        cooldown = float(row["cooldown"])
        last_state = False
        last_trigger_at = None
        had_healthy = False
        unhealthy = 0

        try:
            while True:
                # get_entity_info NO lanza si el socket murio: devuelve RustError
                # o una respuesta de fallo. Contamos respuestas fallidas seguidas
                # y forzamos reconexion al llegar a RECONNECT_AFTER.
                try:
                    entity = await socket.get_entity_info(row["entity_id"])
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    unhealthy += 1
                    self.log("warn", f"Error temporal: {exc}")
                    if unhealthy >= RECONNECT_AFTER:
                        return had_healthy
                    await asyncio.sleep(interval)
                    continue

                self.last_check = time.time()

                if isinstance(entity, RustError):
                    unhealthy += 1
                    if self.status != "error":
                        self.status = "error"
                        self.detail = f"Rust+ dice: {entity.reason}"
                        self.log("warn",
                                 f"Rust+ respondio '{entity.reason}'."
                                 " Revisa el Entity ID (cambia con cada wipe).")
                    if unhealthy >= RECONNECT_AFTER:
                        return had_healthy
                else:
                    had_healthy = True
                    unhealthy = 0
                    if self.status != "running":
                        self.status = "running"
                        self.detail = "Conectado"
                    value = bool(entity.value)
                    self.alarm_on = value

                    if value and not last_state:
                        now = time.monotonic()
                        if last_trigger_at is None or now - last_trigger_at >= cooldown:
                            last_trigger_at = now
                            self.trigger_count += 1
                            self.last_trigger = time.time()
                            self.log("alarm", "ALARMA ACTIVADA")
                            await self._notify()
                        else:
                            self.log("warn", "Alarma activada (en cooldown, sin aviso)")
                    elif last_state and not value:
                        self.log("info", "Alarma desactivada")

                    last_state = value

                await asyncio.sleep(interval)
        finally:
            try:
                await socket.disconnect()
            except Exception:
                pass

    async def _notify(self):
        webhook = self.row["discord_webhook"]
        if not webhook:
            self.log("warn", "Sin webhook de Discord configurado: no hay aviso")
            return
        try:
            await send_discord(
                webhook,
                alarm_name=self.row["name"],
                server=f"{self.row['ip']}:{self.row['port']}",
            )
            self.log("ok", "Aviso enviado a Discord")
        except Exception:
            # El exc puede traer la URL del webhook (secreto): no lo logueamos.
            self.log("error", "Discord rechazo el aviso")


class Manager:
    def __init__(self):
        self.runners: dict[int, AlarmRunner] = {}
        self._sync_task = None
        self._lock = asyncio.Lock()

    async def start(self):
        await self.sync()
        self._sync_task = asyncio.create_task(self._periodic())

    async def shutdown(self):
        if self._sync_task:
            self._sync_task.cancel()
        for runner in list(self.runners.values()):
            if runner.task:
                runner.task.cancel()
        self.runners.clear()

    async def _periodic(self):
        while True:
            await asyncio.sleep(SYNC_INTERVAL)
            try:
                await self.sync()
            except Exception:
                logging.exception("sync fallo")

    async def sync(self):
        """Reconciliar DB contra corutinas vivas."""
        async with self._lock:
            rows = await asyncio.to_thread(db.active_alarms)
            wanted = {row["id"]: row for row in rows}

            # cortar las que sobran o cambiaron
            for alarm_id in list(self.runners):
                runner = self.runners[alarm_id]
                row = wanted.get(alarm_id)
                if row is None or row["updated_at"] != runner.updated_at:
                    if runner.task:
                        runner.task.cancel()
                    del self.runners[alarm_id]

            # arrancar las que faltan
            for alarm_id, row in wanted.items():
                if alarm_id not in self.runners:
                    runner = AlarmRunner(row)
                    runner.task = asyncio.create_task(runner.run())
                    self.runners[alarm_id] = runner

    def snapshot_for(self, alarm_ids):
        out = {}
        for alarm_id in alarm_ids:
            runner = self.runners.get(alarm_id)
            out[alarm_id] = runner.snapshot() if runner else {
                "status": "stopped", "detail": "Deshabilitada", "alarm_on": False,
                "last_check": None, "last_trigger": None, "trigger_count": 0,
                "logs": [],
            }
        return out


manager = Manager()
