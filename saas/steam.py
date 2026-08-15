"""Login con Steam via OpenID 2.0. No requiere API key de Steam.

Flujo:
  1. login_url() manda al usuario a steamcommunity.com a autenticarse.
  2. Steam redirige de vuelta a BASE_URL/auth/steam/return con firma.
  3. verify() reenvia los parametros a Steam con mode=check_authentication;
     Steam contesta is_valid:true y de ahi sale el SteamID64.
"""

import re
from urllib.parse import urlencode

import httpx

from .config import BASE_URL

STEAM_OPENID = "https://steamcommunity.com/openid/login"
RETURN_PATH = "/auth/steam/return"

_CLAIMED_ID = re.compile(r"^https?://steamcommunity\.com/openid/id/(\d{17})$")


def login_url(state: str) -> str:
    # El state viaja dentro de return_to, que Steam firma y devuelve intacto.
    # Al volver comparamos contra la cookie: bloquea el login-CSRF (que un
    # atacante te loguee con SU cuenta).
    return_to = f"{BASE_URL}{RETURN_PATH}?{urlencode({'state': state})}"
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to,
        "openid.realm": BASE_URL,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }
    return f"{STEAM_OPENID}?{urlencode(params)}"


async def verify(query_params) -> str | None:
    """Devuelve el SteamID64 (str) o None si la firma no valida."""
    params = {k: v for k, v in query_params.items() if k.startswith("openid.")}

    if params.get("openid.mode") != "id_res":
        return None
    if not str(params.get("openid.return_to", "")).startswith(BASE_URL + RETURN_PATH):
        return None

    claimed = params.get("openid.claimed_id", "")
    match = _CLAIMED_ID.match(claimed)
    if not match:
        return None
    steam_id = match.group(1)

    params["openid.mode"] = "check_authentication"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(STEAM_OPENID, data=params)

    if response.status_code == 200 and "is_valid:true" in response.text:
        return steam_id
    return None
