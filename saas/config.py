"""Configuracion del servicio via variables de entorno, con defaults sanos.

Variables:
  RUSTALARM_BASE_URL     URL publica del sitio (para el retorno de Steam).
                         Default http://127.0.0.1:8000 (pruebas locales).
  RUSTALARM_HOST         Interfaz de escucha. Default 127.0.0.1.
  RUSTALARM_PORT         Puerto. Default 8000.
  RUSTALARM_ADMIN_STEAM_ID  SteamID64 del dueno del servicio (ve /admin).
  RUSTALARM_MAX_ALARMS   Alarmas por usuario. Default 3.
  RUSTALARM_DATA_DIR     Carpeta de datos. Default ./saas_data.

Las sesiones son tokens aleatorios guardados en la base (no cookies firmadas),
asi que no hace falta un secreto de firma.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("RUSTALARM_DATA_DIR", BASE_DIR / "saas_data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "rustalarm.db"

BASE_URL = os.environ.get("RUSTALARM_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
HOST = os.environ.get("RUSTALARM_HOST", "127.0.0.1")
PORT = int(os.environ.get("RUSTALARM_PORT", "8000"))

ADMIN_STEAM_ID = os.environ.get("RUSTALARM_ADMIN_STEAM_ID", "").strip()
MAX_ALARMS = int(os.environ.get("RUSTALARM_MAX_ALARMS", "3"))

SESSION_COOKIE = "rustalarm_session"
SESSION_DAYS = 30
