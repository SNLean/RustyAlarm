"""python -m saas — arranca el servicio."""

import uvicorn

from .config import HOST, PORT


def main():
    uvicorn.run("saas.app:app", host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
