"""Aviso por Discord webhook."""

import time

import httpx

EMBED_COLOR_ALARM = 0xCE422B
EMBED_COLOR_TEST = 0x6FBF73


async def send_discord(webhook_url: str, *, alarm_name: str, server: str,
                       test: bool = False) -> None:
    """Manda el embed al webhook. Levanta excepcion si Discord rechaza."""
    if test:
        title = "Prueba de webhook"
        description = f"El webhook de **{alarm_name}** quedo configurado bien."
        color = EMBED_COLOR_TEST
    else:
        title = "ALARMA ACTIVADA"
        description = f"**{alarm_name}** se disparo. Revisa tu base."
        color = EMBED_COLOR_ALARM

    payload = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "fields": [{"name": "Servidor", "value": server, "inline": True}],
            "footer": {"text": "Alarma Rust+"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }]
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(webhook_url, json=payload)
        response.raise_for_status()
