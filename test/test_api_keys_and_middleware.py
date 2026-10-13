import httpx
import pytest
from dotenv import load_dotenv
from fastapi.exceptions import HTTPException
from starlette.requests import Request

from app_middleware.depends.api_key_middleware import api_key_middleware
from app_middleware.depends.auth_middleware import (
    auth_middleware,
    get_current_api_key,
    get_current_user,
)
from core.security import TokenManager
from core.services_initializer import init_services
from main import app
from repos.v1.api_keys import (
    ApiKeysRepository,
    CreateApiKey,
)
from repos.v1.users import CreateUser, UsersRepository
from services.mongo_collections.v1.api_keys_collection import ApiKeysCollection
from services.mongo_collections.v1.users_collection import UsersCollection


def _build_request(headers_dict: dict[str, str]) -> Request:
    raw_headers = [
        (k.lower().encode("latin-1"), v.encode("latin-1"))
        for k, v in headers_dict.items()
    ]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": raw_headers,
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_api_keys_repository_crud():
    load_dotenv("app/.env")
    await init_services()

    col = ApiKeysCollection.get_instance()._collection
    await col.delete_many({})

    repo = ApiKeysRepository.get_instance()

    # 1. Crear API Key
    created = await repo.create_api_key(
        CreateApiKey(
            name="Power BI Key",
            serviceType="power_bi",
            scopes=["bi:read"],
        ),
        created_by="user_admin",
    )

    assert created.id.startswith("key_")
    assert created.key.startswith("srm_live_")
    assert created.rawKey == created.key
    assert created.maskedKey.startswith("srm_live_")
    assert created.maskedKey.endswith(created.key[-4:])
    assert "..." in created.maskedKey
    assert created.isActive is True
    assert created.isDeleted is False
    assert created.createdBy == "user_admin"

    # 2. Consultar por ID y Listar
    fetched = await repo.get_api_key_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id

    all_keys = await repo.get_all_api_keys()
    assert len(all_keys) == 1
    assert all_keys[0].id == created.id

    # 3. Verificar y obtener por valor crudo (actualiza lastUsedAt)
    verified = await repo.verify_and_get_key(created.rawKey)
    assert verified is not None
    assert verified.id == created.id
    assert verified.lastUsedAt is not None

    # 4. Toggle desactivar
    toggled = await repo.toggle_api_key_status(created.id, False)
    assert toggled is not None
    assert toggled.isActive is False

    # Al estar inactiva, verify_and_get_key debe retornar None
    assert await repo.verify_and_get_key(created.rawKey) is None

    # Toggle reactivar
    toggled_back = await repo.toggle_api_key_status(created.id, True)
    assert toggled_back is not None
    assert toggled_back.isActive is True
    assert await repo.verify_and_get_key(created.rawKey) is not None

    # 5. Soft Delete
    deleted = await repo.delete_api_key(created.id)
    assert deleted is not None
    assert deleted.isDeleted is True
    assert deleted.isActive is False

    # Verificación posterior a borrado lógico
    assert await repo.verify_and_get_key(created.rawKey) is None
    remaining_keys = await repo.get_all_api_keys()
    assert len(remaining_keys) == 0


@pytest.mark.asyncio
async def test_auth_middleware_unified():
    load_dotenv("app/.env")
    await init_services()

    await ApiKeysCollection.get_instance()._collection.delete_many({})
    await UsersCollection.get_instance()._collection.delete_many({})

    repo_keys = ApiKeysRepository.get_instance()
    repo_users = UsersRepository.get_instance()

    # Crear una API Key de prueba
    api_key_obj = await repo_keys.create_api_key(
        CreateApiKey(name="Integration Key")
    )

    # Crear un Usuario de prueba
    user_obj = await repo_users.create_user(
        CreateUser(
            username="medico_test",
            password="password123",
            name="Dr. Medico Test",
            role="medico",
        )
    )
    user_token = TokenManager.create_session_token(
        user_id=user_obj.id,
        username=user_obj.username,
        role=user_obj.role,
    )

    # Caso A: Header X-API-KEY válido
    req_a = _build_request({"X-API-KEY": api_key_obj.rawKey})
    await auth_middleware(req_a)
    assert req_a.state.auth_type == "api_key"
    current_key_a = get_current_api_key(req_a)
    assert current_key_a is not None
    assert current_key_a.id == api_key_obj.id
    assert get_current_user(req_a) is None

    # Caso B: Header Authorization con prefijo Api-Key válido
    req_b = _build_request({"Authorization": f"Api-Key {api_key_obj.rawKey}"})
    await auth_middleware(req_b)
    assert req_b.state.auth_type == "api_key"
    current_key_b = get_current_api_key(req_b)
    assert current_key_b is not None
    assert current_key_b.id == api_key_obj.id

    # Caso C: Header Authorization con Bearer JWT válido
    req_c = _build_request({"Authorization": f"Bearer {user_token}"})
    await auth_middleware(req_c)
    assert req_c.state.auth_type == "bearer"
    current_user_c = get_current_user(req_c)
    assert current_user_c is not None
    assert current_user_c.id == user_obj.id
    assert req_c.state.user_id == user_obj.id
    assert get_current_api_key(req_c) is None

    # Caso D: API Key inválida -> 401
    req_d = _build_request({"X-API-KEY": "srm_live_invalidkey123"})
    with pytest.raises(HTTPException) as exc_d:
        await auth_middleware(req_d)
    assert exc_d.value.status_code == 401
    assert "Llave API inválida" in exc_d.value.detail

    # Caso E: Bearer token inválido -> 401
    req_e = _build_request({"Authorization": "Bearer invalid.jwt.token"})
    with pytest.raises(HTTPException) as exc_e:
        await auth_middleware(req_e)
    assert exc_e.value.status_code == 401

    # Caso F: Sin encabezados -> 401
    req_f = _build_request({})
    with pytest.raises(HTTPException) as exc_f:
        await auth_middleware(req_f)
    assert exc_f.value.status_code == 401


@pytest.mark.asyncio
async def test_api_key_middleware_dedicated():
    load_dotenv("app/.env")
    await init_services()

    col = ApiKeysCollection.get_instance()._collection
    await col.delete_many({})

    repo_keys = ApiKeysRepository.get_instance()
    api_key_obj = await repo_keys.create_api_key(
        CreateApiKey(name="Dedicated Key")
    )

    req_valid = _build_request({"X-API-KEY": api_key_obj.rawKey})
    res_key = await api_key_middleware(req_valid)
    assert res_key.id == api_key_obj.id

    req_missing = _build_request({})
    with pytest.raises(HTTPException) as exc_missing:
        await api_key_middleware(req_missing)
    assert exc_missing.value.status_code == 401


@pytest.mark.asyncio
async def test_api_keys_http_endpoints():
    load_dotenv("app/.env")
    await init_services()

    await ApiKeysCollection.get_instance()._collection.delete_many({})
    await UsersCollection.get_instance()._collection.delete_many({})

    repo_users = UsersRepository.get_instance()
    user = await repo_users.create_user(
        CreateUser(
            username="admin_api",
            password="password123",
            name="Admin API",
            role="admin",
        )
    )
    token = TokenManager.create_session_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
    )

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Petición sin auth -> 401
        res_unauth = await client.get("/api/v1/api-keys")
        assert res_unauth.status_code == 401

        # 2. Crear API Key
        create_payload = {
            "name": "PowerBI Service",
            "serviceType": "power_bi",
            "scopes": ["bi:read"],
        }
        res_create = await client.post(
            "/api/v1/api-keys", json=create_payload, headers=headers
        )
        assert res_create.status_code == 201
        created_data = res_create.json()
        assert "rawKey" in created_data
        key_id = created_data["id"]
        raw_key = created_data["rawKey"]

        # 3. Listar API Keys
        res_list = await client.get("/api/v1/api-keys", headers=headers)
        assert res_list.status_code == 200
        list_data = res_list.json()
        assert list_data["count"] == 1
        assert list_data["data"][0]["id"] == key_id

        # 4. Probar que la API Key recién creada puede autenticar llamadas GET /api/v1/api-keys
        res_via_key = await client.get(
            "/api/v1/api-keys", headers={"X-API-KEY": raw_key}
        )
        assert res_via_key.status_code == 200

        # 5. Toggle status
        res_toggle = await client.patch(
            f"/api/v1/api-keys/{key_id}/toggle",
            json={"isActive": False},
            headers=headers,
        )
        assert res_toggle.status_code == 200
        assert res_toggle.json()["isActive"] is False

        # Con la llave desactivada, la petición vía X-API-KEY debe fallar (401)
        res_via_deactivated = await client.get(
            "/api/v1/api-keys", headers={"X-API-KEY": raw_key}
        )
        assert res_via_deactivated.status_code == 401

        # 6. Eliminar (soft delete)
        res_delete = await client.delete(
            f"/api/v1/api-keys/{key_id}", headers=headers
        )
        assert res_delete.status_code == 200
        assert res_delete.json()["isDeleted"] is True

        # Verificar lista vacía
        res_list_after = await client.get("/api/v1/api-keys", headers=headers)
        assert res_list_after.json()["count"] == 0
