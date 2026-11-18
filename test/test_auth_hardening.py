import httpx
import pytest
from dotenv import load_dotenv

from main import app
from serum.core.default_values.create_root_user import create_root_user
from serum.core.security import TokenManager
from serum.repos.v1.users import CreateUser, UsersRepository
from serum.services.mongo_collections.v1.users_collection import UsersCollection
from serum.services_initializer import init_services


@pytest.mark.asyncio
async def test_protected_routers_require_authentication_and_admin_roles():
    load_dotenv("app/.env")
    await init_services()

    await UsersCollection.get_instance()._collection.delete_many({})
    await create_root_user()
    users_repo = UsersRepository.get_instance()
    operator = await users_repo.create_user(
        CreateUser(
            username="op_hardening",
            password="Password123!",
            name="Operador Hardening",
            role="Operador",
            accessLevel=3,
        )
    )
    op_token = TokenManager.create_session_token(
        user_id=operator.id,
        username=operator.username,
        role=operator.role,
        access_level=operator.accessLevel,
        tenant="SerumDB",
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        unauth_gets = [
            "/api/v1/patients",
            "/api/v1/doctors",
            "/api/v1/quotations",
            "/api/v1/lab-tests",
            "/api/v1/lab-test-accounts",
            "/api/v1/cash-movements",
            "/api/v1/cash-registers",
            "/api/v1/cash-shifts/current?user_id=root",
            "/api/v1/cash-transactions",
            "/api/v1/receipts",
            "/api/v1/reports/financial?start_date=0&end_date=1",
            "/api/v1/branches",
            "/api/v1/app-settings/current",
            "/api/v1/roles",
            "/api/v1/api-keys",
        ]
        for path in unauth_gets:
            res = await client.get(path, headers={"X-Servin": "SerumDB"})
            assert res.status_code == 401, f"Expected 401 for GET {path}, got {res.status_code}"

        # Operador (nivel 3) no puede acceder a rutas administrativas
        op_headers = {
            "X-Servin": "SerumDB",
            "Authorization": f"Bearer {op_token}",
        }
        assert (await client.get("/api/v1/api-keys", headers=op_headers)).status_code == 403
        assert (
            await client.patch(
                "/api/v1/app-settings/Default",
                json={"currency": "USD"},
                headers=op_headers,
            )
        ).status_code == 403
        assert (
            await client.post(
                "/api/v1/roles",
                json={"name": "FakeAdmin", "accessLevel": 5},
                headers=op_headers,
            )
        ).status_code == 403
        assert (
            await client.patch(
                "/api/v1/branches/ORIGIN_BRANCH",
                json={"name": "Hacked"},
                headers=op_headers,
            )
        ).status_code == 403


@pytest.mark.asyncio
async def test_jwt_tenant_claim_transition_session_type_and_user_status():
    load_dotenv("app/.env")
    await init_services()

    await UsersCollection.get_instance()._collection.delete_many({})
    users_repo = UsersRepository.get_instance()

    active_user = await users_repo.create_user(
        CreateUser(
            username="active_user",
            password="Password123!",
            name="Usuario Activo",
            role="Operador",
            accessLevel=3,
        )
    )
    inactive_user = await users_repo.create_user(
        CreateUser(
            username="inactive_user",
            password="Password123!",
            name="Usuario Inactivo",
            role="Operador",
            accessLevel=3,
            isActive=False,
        )
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        # 1. Login exitoso incluye tenant en session y refresh token
        res_login = await client.post(
            "/api/v1/auths/login",
            json={"username": "active_user", "password": "Password123!"},
            headers={"X-Servin": "SerumDB"},
        )
        assert res_login.status_code == 200
        tokens = res_login.json()
        session_payload = TokenManager.decode_token(tokens["token"])
        refresh_payload = TokenManager.decode_token(tokens["refreshToken"])
        assert session_payload is not None
        assert refresh_payload is not None
        assert session_payload.get("tenant") == "SerumDB"
        assert refresh_payload.get("tenant") == "SerumDB"

        # 2. Mismo tenant -> 200 OK
        res_ok = await client.get(
            "/api/v1/patients",
            headers={
                "X-Servin": "SerumDB",
                "Authorization": f"Bearer {tokens['token']}",
            },
        )
        assert res_ok.status_code == 200

        # 3. Tenant distinto al del JWT -> 401 Unauthorized
        res_cross = await client.get(
            "/api/v1/patients",
            headers={
                "X-Servin": "OtroTenant",
                "Authorization": f"Bearer {tokens['token']}",
            },
        )
        assert res_cross.status_code == 401

        # 4. Token legacy sin claim tenant -> permitido temporalmente en modo transición
        legacy_token = TokenManager.create_session_token(
            user_id=active_user.id,
            username=active_user.username,
            role=active_user.role,
            access_level=active_user.accessLevel,
        )
        res_legacy = await client.get(
            "/api/v1/patients",
            headers={
                "X-Servin": "SerumDB",
                "Authorization": f"Bearer {legacy_token}",
            },
        )
        assert res_legacy.status_code == 200

        # 5. Refresh token usado como Bearer en endpoint de negocio -> 401 Unauthorized
        res_refresh_as_bearer = await client.get(
            "/api/v1/patients",
            headers={
                "X-Servin": "SerumDB",
                "Authorization": f"Bearer {tokens['refreshToken']}",
            },
        )
        assert res_refresh_as_bearer.status_code == 401

        # 6. Usuario inactivo no puede hacer login ni refresh-token
        res_inactive_login = await client.post(
            "/api/v1/auths/login",
            json={"username": "inactive_user", "password": "Password123!"},
            headers={"X-Servin": "SerumDB"},
        )
        assert res_inactive_login.status_code == 401

        inactive_refresh = TokenManager.create_refresh_token(
            user_id=inactive_user.id,
            username=inactive_user.username,
            role=inactive_user.role,
            access_level=inactive_user.accessLevel,
            tenant="SerumDB",
        )
        res_inactive_refresh = await client.post(
            "/api/v1/auths/refresh-token",
            json={"refreshToken": inactive_refresh},
            headers={"X-Servin": "SerumDB"},
        )
        assert res_inactive_refresh.status_code == 401
