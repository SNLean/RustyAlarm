"""Catalogo de sonidos de alarma.

Dos fuentes:
  - built-in: los que vienen en el repo (saas/assets/sounds), solo lectura.
  - subidos por el admin: en DATA_DIR/sounds (se pueden borrar).

El campo `sound` de cada alarma guarda solo el nombre de archivo; el panel lo
reproduce cuando la alarma se dispara y la pagina esta abierta. `resolve()`
blinda contra path traversal: nunca se arma una ruta con lo que manda el cliente
sin pasar por aca.
"""

import re
from pathlib import Path

from .config import DATA_DIR

BUILTIN_DIR = Path(__file__).parent / "assets" / "sounds"
UPLOAD_DIR = DATA_DIR / "sounds"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".mp3", ".ogg", ".wav"}
MAX_BYTES = 2 * 1024 * 1024          # 2 MB por sonido
DEFAULT_SOUND = "sirena.wav"

_NAME_RE = re.compile(r"^[a-z0-9._-]+\.(mp3|ogg|wav)$")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _display_name(filename: str) -> str:
    stem = Path(filename).stem.replace("_", " ").replace("-", " ").strip()
    return (stem[:1].upper() + stem[1:]) if stem else filename


def is_safe_name(filename: str) -> bool:
    """Nombre de archivo aceptable: basename, chars seguros, extension de audio.
    No valida existencia (eso es resolve)."""
    return bool(filename) and filename == Path(filename).name \
        and bool(_NAME_RE.match(filename))


def catalog() -> list[dict]:
    """Sonidos disponibles: [{file, name, builtin}]. Un subido con el mismo
    nombre que un built-in lo pisa."""
    out: dict[str, dict] = {}
    for f in sorted(UPLOAD_DIR.glob("*")):
        if f.is_file() and f.suffix.lower() in ALLOWED_EXT:
            out[f.name] = {"file": f.name, "name": _display_name(f.name), "builtin": False}
    for f in sorted(BUILTIN_DIR.glob("*")):
        if f.is_file() and f.suffix.lower() in ALLOWED_EXT and f.name not in out:
            out[f.name] = {"file": f.name, "name": _display_name(f.name), "builtin": True}
    return list(out.values())


def resolve(filename: str):
    """Ruta real del archivo a servir, o None. Rechaza cualquier cosa que no sea
    un basename seguro con extension de audio, y solo devuelve si existe."""
    if not is_safe_name(filename):
        return None
    up = UPLOAD_DIR / filename
    if up.is_file():
        return up
    bi = BUILTIN_DIR / filename
    if bi.is_file():
        return bi
    return None


def is_valid(filename: str) -> bool:
    return resolve(filename) is not None


def default_sound() -> str:
    """Un nombre valido para usar por defecto (el built-in preferido, o el
    primero del catalogo)."""
    if is_valid(DEFAULT_SOUND):
        return DEFAULT_SOUND
    cat = catalog()
    return cat[0]["file"] if cat else ""


def upload_filename(display_name: str, original: str) -> str:
    """Nombre de archivo seguro para un sonido subido, a partir del nombre que
    puso el admin y la extension del original."""
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_EXT:
        ext = ".mp3"
    slug = _SLUG_RE.sub("-", (display_name or "").strip().lower()).strip("-")[:40]
    return (slug or "sonido") + ext


def save_upload(filename: str, data: bytes) -> None:
    """Guarda un sonido subido. Asume filename ya saneado por upload_filename."""
    if not is_safe_name(filename):
        raise ValueError("nombre invalido")
    if len(data) > MAX_BYTES:
        raise ValueError("archivo demasiado grande")
    (UPLOAD_DIR / filename).write_bytes(data)


def delete_upload(filename: str) -> bool:
    """Borra un sonido SUBIDO (nunca un built-in). True si borro algo."""
    if not is_safe_name(filename):
        return False
    path = UPLOAD_DIR / filename
    if path.is_file():
        path.unlink()
        return True
    return False
