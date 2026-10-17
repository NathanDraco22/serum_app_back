from fastapi import Request, status
from fastapi.exceptions import HTTPException

from serum.repos.v1.api_keys import ApiKeyInDb, ApiKeysRepository


async def api_key_middleware(req: Request) -> ApiKeyInDb:
    api_key_value = req.headers.get("X-API-KEY") or req.headers.get("x-api-key")

    if not api_key_value:
        auth_header = req.headers.get("Authorization") or req.headers.get(
            "authorization"
        )
        if auth_header and auth_header.startswith("Api-Key "):
            api_key_value = auth_header.replace("Api-Key ", "").strip()

    if not api_key_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Encabezado X-API-KEY faltante",
        )

    api_key = await ApiKeysRepository.get_instance().verify_and_get_key(
        api_key_value
    )

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Llave Serum API Key inválida o inactiva",
        )

    req.state.api_key = api_key
    req.state.auth_type = "api_key"
    return api_key
