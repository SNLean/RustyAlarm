"""python -m saas — arranca el servicio.

IMPORTANTE: un solo proceso, un solo worker. El monitor guarda estado en
memoria (manager + runners); con varios workers cada uno abriria TODAS las
alarmas => alertas de Discord duplicadas y N conexiones por alarma. No agregar
--workers ni gunicorn con varios procesos.
"""

import os

import uvicorn

from .config import HOST, PORT

# nginx corre en localhost y reenvia X-Forwarded-Proto/For. forwarded_allow_ips
# limita en quien confiamos para esos headers (el proxy local).
FORWARDED_IPS = os.environ.get("RUSTALARM_FORWARDED_IPS", "127.0.0.1")


def main():
    uvicorn.run(
        "saas.app:app",
        host=HOST,
        port=PORT,
        log_level="warning",
        proxy_headers=True,
        forwarded_allow_ips=FORWARDED_IPS,
    )


if __name__ == "__main__":
    main()
