from fastapi import Request, status
from fastapi.exceptions import HTTPException

from serum.core.security import TokenManager
from serum.repos.v1.api_keys import ApiKeyInDb, ApiKeysRepository
from serum.repos.v1.users import UserInDb, UsersRepository


async def auth_middleware(req: Request) -> None:
    """Middleware unificado de autenticación.

    Permite acceso mediante:
    1. Header de API Key ('X-API-KEY' o 'Authorization: Api-Key <token>').
    2. Header Bearer JWT ('Authorization: Bearer <token>').
    Si no se proporciona ninguno o alguno de ellos es inválido/inactivo, rechaza con HTTP 401.
    """
    # 1. Evaluación de API Key
    api_key_value = req.headers.get("X-API-KEY") or req.headers.get("x-api-key")
    if not api_key_value:
        auth_header = req.headers.get("Authorization") or req.headers.get(
            "authorization"
        )
        if auth_header and auth_header.startswith("Api-Key "):
            api_key_value = auth_header.replace("Api-Key ", "").strip()

    if api_key_value:
        api_key = await ApiKeysRepository.get_instance().verify_and_get_key(
            api_key_value
        )
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Llave API inválida o inactiva",
            )
        req.state.api_key = api_key
        req.state.auth_type = "api_key"
        req.state.user = None
        req.state.user_id = None
        return

    # 2. Evaluación de Bearer Token (JWT de usuario)
    auth_header = req.headers.get("Authorization") or req.headers.get(
        "authorization"
    )
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()
        payload = TokenManager.decode_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de sesión inválido o expirado",
            )

        user_id = payload.get("userId")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no contiene un identificador de usuario válido",
            )

        user = await UsersRepository.get_instance().get_user_by_id(user_id)
        if user is None or not user.isActive or user.isDeleted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
            )

        req.state.user = user
        req.state.user_id = user.id
        req.state.auth_type = "bearer"
        req.state.api_key = None
        return

    # 3. Ningún método de autenticación proporcionado
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado: Encabezado de autenticación faltante (se requiere Bearer o X-API-KEY)",
    )


def get_current_user(req: Request) -> UserInDb | None:
    """Helper para obtener el usuario autenticado desde el estado del request."""
    return getattr(req.state, "user", None)


def get_current_api_key(req: Request) -> ApiKeyInDb | None:
    """Helper para obtener el API Key autenticado desde el estado del request."""
    return getattr(req.state, "api_key", None)
