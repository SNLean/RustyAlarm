"""Panel web local para configurar y controlar el monitor de alarma Rust+.

Servidor de biblioteca estandar, sin dependencias extra. Escucha solo en
127.0.0.1 y sirve una unica pagina con el formulario de configuracion, los
botones de arranque/parada y el log en vivo.

    python webapp.py [--port 8765] [--no-browser]
"""

import argparse
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from core import (
    CONFIG_PATH,
    AlarmMonitor,
    ConfigError,
    bundle_dir,
    config_for_client,
    load_config,
    play_sound,
    save_config,
    sound_path,
    stop_sound,
)

HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_BODY = 64 * 1024

monitor = AlarmMonitor()
_start_lock = threading.Lock()


def index_html():
    path = bundle_dir() / "web" / "index.html"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class Handler(BaseHTTPRequestHandler):
    server_version = "RustAlarmPanel/1.0"
    protocol_version = "HTTP/1.1"

    # ---- helpers ----

    def log_message(self, *args):
        pass  # el log util es el del monitor, no el de acceso HTTP

    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        # Endurecimiento del panel local (clickjacking / sniffing).
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline';"
            " script-src 'self' 'unsafe-inline'; img-src 'self' data:;"
            " frame-ancestors 'none'; base-uri 'none'",
        )
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        if length > MAX_BODY:
            raise ValueError("Cuerpo demasiado grande")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _host_ok(self):
        """Rechaza peticiones con Host ajeno (proteccion DNS rebinding)."""
        host = (self.headers.get("Host") or "").split(":")[0].strip("[]")
        return host in ("127.0.0.1", "localhost", "::1", "")

    def _csrf_ok(self):
        """Bloquea CSRF cross-site contra el panel local. El check de Host no
        alcanza: una web maliciosa puede mandar un POST 'simple' (text/plain,
        sin preflight) a 127.0.0.1:8765. Exigir application/json fuerza el
        preflight de CORS (que no respondemos) y validamos el Origin si viene."""
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if ctype != "application/json":
            return False
        origin = self.headers.get("Origin")
        if origin:
            port = self.server.server_address[1]
            allowed = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
            if origin not in allowed:
                return False
        return True

    def _state(self, since=0):
        wav = sound_path()
        return {
            "config": config_for_client(load_config()),
            "config_path": str(CONFIG_PATH),
            "sound_path": str(wav),
            "sound_exists": wav.exists(),
            "monitor": monitor.snapshot(),
            "logs": monitor.logs_since(since),
        }

    # ---- rutas ----

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "Host no permitido"})
        url = urlparse(self.path)

        if url.path in ("/", "/index.html"):
            try:
                return self._send(200, index_html(), "text/html; charset=utf-8")
            except FileNotFoundError:
                return self._send(500, "Falta web/index.html", "text/plain; charset=utf-8")

        if url.path == "/api/state":
            since = parse_qs(url.query).get("since", ["0"])[0]
            try:
                since = int(since)
            except ValueError:
                since = 0
            return self._send(200, self._state(since))

        return self._send(404, {"error": "No encontrado"})

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, {"error": "Host no permitido"})
        if not self._csrf_ok():
            return self._send(403, {"error": "Solicitud cross-site rechazada"})
        path = urlparse(self.path).path

        try:
            payload = self._read_json()
        except ValueError as exc:
            return self._send(400, {"error": f"JSON invalido: {exc}"})

        if path == "/api/config":
            try:
                save_config(payload)
            except ConfigError as exc:
                return self._send(400, {"error": "Revisa los campos marcados",
                                        "errors": exc.errors})
            except OSError as exc:
                return self._send(500, {"error": f"No se pudo guardar: {exc}"})
            return self._send(200, {"ok": True, "state": self._state()})

        if path == "/api/monitor/start":
            with _start_lock:
                if monitor.running:
                    return self._send(409, {"error": "El monitor ya esta corriendo"})
                try:
                    config = save_config(payload) if payload else load_config()
                    monitor.start(config)
                except ConfigError as exc:
                    return self._send(400, {"error": "Revisa los campos marcados",
                                            "errors": exc.errors})
                except (OSError, RuntimeError) as exc:
                    return self._send(400, {"error": str(exc)})
            return self._send(200, {"ok": True, "state": self._state()})

        if path == "/api/monitor/stop":
            monitor.stop()
            stop_sound()
            return self._send(200, {"ok": True, "state": self._state()})

        if path == "/api/sound/test":
            try:
                play_sound()
            except Exception as exc:
                return self._send(400, {"error": str(exc)})
            monitor.log("info", "Prueba de sonido")
            return self._send(200, {"ok": True})

        if path == "/api/sound/stop":
            stop_sound()
            return self._send(200, {"ok": True})

        return self._send(404, {"error": "No encontrado"})


def serve(port=DEFAULT_PORT, open_browser=True):
    try:
        httpd = ThreadingHTTPServer((HOST, port), Handler)
    except OSError as exc:
        print(f"No se pudo abrir el puerto {port}: {exc}")
        return 1

    url = f"http://{HOST}:{port}/"
    print(f"Panel disponible en {url}")
    print(f"Config: {CONFIG_PATH}")
    print("Ctrl+C para cerrar.")

    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando...")
    finally:
        monitor.stop()
        stop_sound()
        httpd.server_close()
    return 0


def main():
    parser = argparse.ArgumentParser(description="Panel de configuracion Rust+")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true",
                        help="No abrir el navegador al arrancar")
    args = parser.parse_args()
    return serve(args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    sys.exit(main())
