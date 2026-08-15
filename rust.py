"""Monitor de alarma Rust+ en modo consola.

Para el panel web con formulario de configuracion, usar `python webapp.py`.
"""

import sys
import time

from core import AlarmMonitor, ConfigError, load_config, validate_config

ICONS = {
    "info": "i",
    "ok": "OK",
    "warn": "!",
    "error": "X",
    "alarm": ">>>",
}


def print_log(entry):
    stamp = time.strftime("%H:%M:%S", time.localtime(entry["ts"]))
    icon = ICONS.get(entry["level"], "-")
    print(f"[{stamp}] {icon} {entry['message']}", flush=True)


def main():
    try:
        config = validate_config(load_config())
    except FileNotFoundError:
        print("No se encontro config.json. Ejecuta 'python webapp.py' para crearlo.")
        return 1
    except ConfigError as exc:
        print("config.json tiene errores:")
        for field, message in exc.errors.items():
            print(f"  - {field}: {message}")
        print("Ejecuta 'python webapp.py' para corregirlos desde el navegador.")
        return 1

    monitor = AlarmMonitor(on_log=print_log)
    monitor.start(config)

    try:
        while monitor.running:
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\nCerrando...")
        monitor.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
