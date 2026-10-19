import time
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
import jwt
import pytest

from serum.core.security import TokenManager
from serum.repos.v1.users import CreateUser, UsersRepository
from serum.serum_config import SerumContext, serumCtx
from serum.services_initializer import init_services
from main import app

SERVICE_PRIVATE_KEY = b"""-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIC/59CJbQp5CtZFY5nfFGkjWdxDK0omREIeUHmObC09B
-----END PRIVATE KEY-----
"""


def encode_super_token(payload: dict | None = None) -> str:
    if payload is None:
        payload = {
            "sub": "test-super-admin",
            "origin": "Serum Dev Ops",
            "exp": int(time.time()) + 300,
        }
    return jwt.encode(payload, SERVICE_PRIVATE_KEY, algorithm="EdDSA")


@pytest.mark.asyncio
async def test_imports_endpoint_authorization_and_execution():
    load_dotenv("app/.env")
    await init_services()

    transport = ASGITransport(app=app)
    tenant_nickname = "test_import_tenant"
    tenant_headers = {
        "x-tenant-nickname": tenant_nickname,
        "x-branch": "ORIGIN_BRANCH",
    }

    # 1. Crear usuarios de prueba dentro del tenant 'test_import_tenant'
    ctx_token = serumCtx.set(
        SerumContext(businessNickname=tenant_nickname, branchId="ORIGIN_BRANCH")
    )
    try:
        users_repo = UsersRepository.get_instance()
        operator_user = await users_repo.create_user(
            CreateUser(
                username=f"operator_{int(time.time())}",
                name="Operador Laboratorio",
                password="OperatorPassword123",
                role="operator",
                branches=["ORIGIN_BRANCH"],
                accessLevel=2,
            )
        )
        admin_user = await users_repo.create_user(
            CreateUser(
                username=f"admin_{int(time.time())}",
                name="Administrador Laboratorio",
                password="AdminPassword123",
                role="admin",
                branches=["ORIGIN_BRANCH"],
                accessLevel=5,
            )
        )
    finally:
        serumCtx.reset(ctx_token)

    operator_token = TokenManager.create_session_token(
        user_id=operator_user.id,
        username=operator_user.username,
        role=operator_user.role,
        access_level=operator_user.accessLevel,
    )

    admin_token = TokenManager.create_session_token(
        user_id=admin_user.id,
        username=admin_user.username,
        role=admin_user.role,
        access_level=admin_user.accessLevel,
    )

    super_token = encode_super_token()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 2. Petición sin encabezado de autenticación -> 401
        res_no_auth = await client.post(
            "/api/v1/imports/default-catalog",
            headers=tenant_headers,
        )
        assert res_no_auth.status_code == 401
        assert "No autorizado" in res_no_auth.json()["detail"]

        # 3. Petición con usuario de bajo nivel de acceso (accessLevel = 2) -> 403
        res_forbidden = await client.post(
            "/api/v1/imports/default-catalog",
            headers={
                **tenant_headers,
                "Authorization": f"Bearer {operator_token}",
            },
        )
        assert res_forbidden.status_code == 403
        assert "permisos de administrador" in res_forbidden.json()["detail"]

        # 4. Petición con Super Token -> 200 OK
        res_super = await client.post(
            "/api/v1/imports/default-catalog",
            headers={
                **tenant_headers,
                "Authorization": f"Bearer {super_token}",
            },
        )
        assert res_super.status_code == 200
        data = res_super.json()
        assert data["success"] is True
        assert data["totalProcessed"] > 0
        assert data["atomicCreated"] + data["alreadyExisting"] > 0

        # 5. Re-ejecución inmediata (Idempotencia) a través del alias /lab-tests
        res_idempotent = await client.post(
            "/api/v1/imports/lab-tests",
            headers={
                **tenant_headers,
                "Authorization": f"Bearer {super_token}",
            },
        )
        assert res_idempotent.status_code == 200
        data_idem = res_idempotent.json()
        assert data_idem["success"] is True
        assert data_idem["atomicCreated"] == 0
        assert data_idem["packsCreated"] == 0
        assert data_idem["alreadyExisting"] == data_idem["totalProcessed"]

        # 6. Petición con Usuario Administrador (accessLevel = 5) -> 200 OK
        res_admin = await client.post(
            "/api/v1/imports/default-catalog",
            headers={
                **tenant_headers,
                "Authorization": f"Bearer {admin_token}",
            },
        )
        assert res_admin.status_code == 200
        data_admin = res_admin.json()
        assert data_admin["success"] is True
        assert data_admin["alreadyExisting"] == data_admin["totalProcessed"]
