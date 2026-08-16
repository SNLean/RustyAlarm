"""Nucleo compartido: rutas, configuracion y monitor de alarma Rust+.

Este modulo no ejecuta nada al importarse. Lo usan tanto `rust.py` (modo
consola) como `webapp.py` (panel web).
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from collections import deque
from pathlib import Path

from rustplus import RustSocket, ServerDetails
from rustplus.structs.rust_error import RustError

try:
    import winsound
except ImportError:  # pragma: no cover - el proyecto es Windows-only
    winsound = None

# Silenciar logs ruidosos de rustplus
logging.getLogger("rustplus").setLevel(logging.CRITICAL)


# ================= RUTAS =================

def base_dir() -> Path:
    """Carpeta de datos editables (config.json, alarma.wav).

    Congelado con PyInstaller apunta a la carpeta del .exe, no a _MEIPASS,
    porque config.json tiene que poder escribirse y sobrevivir al cierre.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundle_dir() -> Path:
    """Carpeta de recursos de solo lectura empaquetados (web/index.html)."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent


CONFIG_PATH = base_dir() / "config.json"


def sound_path() -> Path:
    """WAV de alarma: primero el de al lado del exe, si no el empaquetado.

    Asi el usuario puede reemplazar el sonido dejando su propio alarma.wav
    junto al ejecutable sin tener que recompilar.
    """
    local = base_dir() / "alarma.wav"
    if local.exists():
        return local
    return bundle_dir() / "alarma.wav"


# ================= CONFIG =================

DEFAULTS = {
    "IP": "",
    "PORT": "28082",
    "STEAM_ID": 0,
    "PLAYER_TOKEN": 0,
    "ALARM_ENTITY_ID": 0,
    "CHECK_INTERVAL": 3,
    "COOLDOWN": 10,
}


class ConfigError(Exception):
    """Config invalida. `errors` mapea campo -> mensaje."""

    def __init__(self, errors):
        super().__init__("Configuracion invalida")
        self.errors = errors


def load_config(path=None):
    """Lee config.json. Si no existe devuelve los valores por defecto."""
    path = Path(path or CONFIG_PATH)
    if not path.exists():
        return dict(DEFAULTS)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in data.items() if k in DEFAULTS})
    return merged


def validate_config(data):
    """Normaliza y valida. Devuelve la config limpia o levanta ConfigError."""
    errors = {}
    clean = dict(DEFAULTS)

    ip = str(data.get("IP", "")).strip()
    if not ip:
        errors["IP"] = "Requerido"
    clean["IP"] = ip

    port = str(data.get("PORT", "")).strip()
    if not port:
        errors["PORT"] = "Requerido"
    elif not port.isdigit() or not (1 <= int(port) <= 65535):
        errors["PORT"] = "Debe ser un numero entre 1 y 65535"
    clean["PORT"] = port

    for field, label in (
        ("STEAM_ID", "Steam ID"),
        ("PLAYER_TOKEN", "Player token"),
        ("ALARM_ENTITY_ID", "Entity ID"),
    ):
        raw = str(data.get(field, "")).strip()
        if not raw:
            errors[field] = "Requerido"
            continue
        try:
            value = int(raw)
        except ValueError:
            errors[field] = f"{label} debe ser un numero entero"
            continue
        if field != "PLAYER_TOKEN" and value <= 0:
            errors[field] = f"{label} debe ser mayor que 0"
            continue
        clean[field] = value

    for field, minimum, label in (
        ("CHECK_INTERVAL", 0.2, "El intervalo"),
        ("COOLDOWN", 0, "El cooldown"),
    ):
        raw = str(data.get(field, "")).strip()
        try:
            value = float(raw)
        except ValueError:
            errors[field] = f"{label} debe ser un numero"
            continue
        if value < minimum:
            errors[field] = f"{label} minimo es {minimum} segundos"
            continue
        clean[field] = int(value) if value == int(value) else value

    if errors:
        raise ConfigError(errors)
    return clean


#: Enteros que exceden Number.MAX_SAFE_INTEGER en JavaScript y por eso viajan
#: al navegador como texto (STEAM_ID ronda 7.6e16 y se redondearia solo).
BIG_INT_FIELDS = ("STEAM_ID", "PLAYER_TOKEN", "ALARM_ENTITY_ID")


def config_for_client(config):
    """Copia de la config con los enteros grandes como string."""
    out = dict(config)
    for field in BIG_INT_FIELDS:
        out[field] = str(out.get(field, ""))
    return out


def save_config(data, path=None):
    """Valida y escribe config.json de forma atomica."""
    clean = validate_config(data)
    path = Path(path or CONFIG_PATH)
    # Temp unico por proceso: dos guardados concurrentes no se pisan el .tmp.
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp.replace(path)
    return clean


# ================= SONIDO =================

def play_sound(path=None):
    """Reproduce el WAV de alarma sin bloquear."""
    path = Path(path or sound_path())
    if winsound is None:
        raise RuntimeError("winsound solo esta disponible en Windows")
    if not path.exists():
        raise FileNotFoundError(f"No se encontro {path.name} en {path.parent}")
    winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)


def stop_sound():
    if winsound is not None:
        winsound.PlaySound(None, winsound.SND_PURGE)


# ================= MONITOR =================

class AlarmMonitor:
    """Corre el bucle de sondeo de Rust+ en un hilo aparte.

    Seguro de usar desde el hilo del servidor web: todo el estado publico se
    lee bajo lock y el corte se pide con `loop.call_soon_threadsafe`.
    """

    def __init__(self, on_log=None):
        self._lock = threading.RLock()
        self._thread = None
        self._loop = None
        self._stop_event = None
        self._logs = deque(maxlen=300)
        self._seq = 0
        self._on_log = on_log

        self.status = "stopped"  # stopped | starting | running | error
        self.detail = ""
        self.alarm_on = False
        self.last_check = None
        self.last_trigger = None
        self.trigger_count = 0

    # ---- logging ----

    def log(self, level, message):
        with self._lock:
            self._seq += 1
            entry = {
                "seq": self._seq,
                "ts": time.time(),
                "level": level,
                "message": str(message),
            }
            self._logs.append(entry)
        if self._on_log:
            self._on_log(entry)
        return entry

    def logs_since(self, seq=0):
        with self._lock:
            return [e for e in self._logs if e["seq"] > seq]

    # ---- estado ----

    @property
    def running(self):
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def snapshot(self):
        with self._lock:
            return {
                "status": self.status,
                "detail": self.detail,
                "running": self._thread is not None and self._thread.is_alive(),
                "alarm_on": self.alarm_on,
                "last_check": self.last_check,
                "last_trigger": self.last_trigger,
                "trigger_count": self.trigger_count,
                "seq": self._seq,
            }

    def _set(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items():
                setattr(self, key, value)

    # ---- ciclo de vida ----

    def start(self, config):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise RuntimeError("El monitor ya esta corriendo")
            config = validate_config(config)
            self.status = "starting"
            self.detail = ""
            self.alarm_on = False
            self._thread = threading.Thread(
                target=self._thread_main, args=(config,), daemon=True
            )
            self._thread.start()
        self.log("info", "Iniciando monitor...")

    def stop(self, timeout=10):
        with self._lock:
            thread = self._thread
            loop = self._loop
            event = self._stop_event
        if thread is None or not thread.is_alive():
            self._set(status="stopped")
            return False
        if loop is not None and event is not None:
            loop.call_soon_threadsafe(event.set)
        thread.join(timeout)
        stopped = not thread.is_alive()
        if not stopped:
            self.log("error", "El monitor no respondio al corte")
        return stopped

    # ---- interno ----

    def _thread_main(self, config):
        try:
            asyncio.run(self._run(config))
        except Exception as exc:  # el hilo nunca debe morir en silencio
            self._set(status="error", detail=str(exc))
            self.log("error", f"El monitor termino con error: {exc}")
        finally:
            with self._lock:
                self._loop = None
                self._stop_event = None
                if self.status not in ("error",):
                    self.status = "stopped"

    async def _run(self, config):
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()
        with self._lock:
            self._loop = loop
            self._stop_event = stop_event

        details = ServerDetails(
            config["IP"],
            config["PORT"],
            config["STEAM_ID"],
            config["PLAYER_TOKEN"],
        )
        socket = RustSocket(details)

        try:
            await socket.connect()
        except Exception as exc:
            self._set(status="error", detail=str(exc))
            self.log("error", f"No se pudo conectar: {exc}")
            return

        self._set(status="running", detail="Conectado a Rust+")
        self.log("ok", "Conectado a Rust+. Escuchando alarma...")

        interval = float(config["CHECK_INTERVAL"])
        cooldown = float(config["COOLDOWN"])
        entity_id = config["ALARM_ENTITY_ID"]
        last_state = False
        last_trigger_at = None

        try:
            while not stop_event.is_set():
                try:
                    entity = await socket.get_entity_info(entity_id)

                    if isinstance(entity, RustError):
                        self.log("warn", f"Rust+ respondio error: {entity.reason}")
                    else:
                        value = bool(entity.value)
                        self._set(last_check=time.time(), alarm_on=value)

                        # ---- DETECCION OFF -> ON ----
                        if value and not last_state:
                            now = time.monotonic()
                            in_cooldown = (
                                last_trigger_at is not None
                                and now - last_trigger_at < cooldown
                            )
                            if in_cooldown:
                                restante = cooldown - (now - last_trigger_at)
                                self.log(
                                    "warn",
                                    f"Alarma activada, en cooldown ({restante:.0f}s)",
                                )
                            else:
                                last_trigger_at = now
                                with self._lock:
                                    self.trigger_count += 1
                                    self.last_trigger = time.time()
                                self.log("alarm", "ALARMA ACTIVADA")
                                try:
                                    play_sound()
                                except Exception as exc:
                                    self.log("error", f"No se pudo sonar: {exc}")
                        elif last_state and not value:
                            self.log("info", "Alarma desactivada")

                        last_state = value

                except Exception as exc:
                    self.log("warn", f"Error temporal: {exc}")

                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=interval)
                except asyncio.TimeoutError:
                    pass
        finally:
            try:
                await socket.disconnect()
            except Exception:
                pass
            self._set(status="stopped", detail="Desconectado", alarm_on=False)
            self.log("info", "Monitor detenido")
