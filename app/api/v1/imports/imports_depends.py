import jwt
from fastapi import Request, status
from fastapi.exceptions import HTTPException

from serum.core.security import TokenManager
from serum.repos.v1.api_keys import ApiKeysRepository
from serum.repos.v1.users import UsersRepository


async def validate_admin_or_super_token(req: Request) -> dict[str, str]:
    """Valida que la petición cuente con autorización de Super Token o Usuario Administrador.

    Permite:
    1. Super Token (firmado con clave pública del sistema / EdDSA).
    2. Header X-API-KEY / Api-Key de una llave activa con rol de administración.
    3. Bearer Token JWT de un usuario con accessLevel >= 4 (Admin) activo en el tenant.
    """
    raw_auth = req.headers.get("Authorization") or req.headers.get("authorization")
    api_key_header = req.headers.get("X-API-KEY") or req.headers.get("x-api-key")

    # 1. Evaluación de Super Token directo (como Bearer o directo)
    if raw_auth:
        token_candidate = raw_auth
        if token_candidate.startswith("Bearer "):
            token_candidate = token_candidate.replace("Bearer ", "").strip()

        try:
            unverified_header = jwt.get_unverified_header(token_candidate)
            token_alg = unverified_header.get("alg")
        except Exception:
            token_alg = None

        if token_alg == "EdDSA":
            super_res = TokenManager.super_token_verify(token_candidate)
            if super_res is not None:
                req.state.auth_type = "super_token"
                req.state.user = None
                return {"auth_type": "super_token"}


    # 2. Evaluación de API Key
    if not api_key_header and raw_auth and raw_auth.startswith("Api-Key "):
        api_key_header = raw_auth.replace("Api-Key ", "").strip()

    if api_key_header:
        api_key = await ApiKeysRepository.get_instance().verify_and_get_key(
            api_key_header
        )
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Llave API inválida o inactiva",
            )
        req.state.api_key = api_key
        req.state.auth_type = "api_key"
        return {"auth_type": "api_key"}

    # 3. Evaluación de Bearer JWT de Usuario
    if raw_auth and raw_auth.startswith("Bearer "):
        token = raw_auth.replace("Bearer ", "").strip()
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

        # Validar permisos de administrador (accessLevel >= 4 o role admin/root)
        is_admin = user.accessLevel >= 4 or user.role.lower() in (
            "admin",
            "administrador",
            "root",
            "superadmin",
        )
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requieren permisos de administrador para ejecutar importaciones",
            )

        req.state.user = user
        req.state.user_id = user.id
        req.state.auth_type = "bearer"
        return {"auth_type": "bearer", "user_id": user.id}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado: Encabezado de autenticación requerido (Super Token o Bearer JWT Administrador)",
    )
