import httpx
import pytest
from dotenv import load_dotenv

from main import app
from serum.core.default_values.create_root_user import create_root_user
from serum.core.security import TokenManager
from serum.repos.v1.users import CreateUser, UsersRepository
from serum.services.mongo_collections.v1.branches_collection import BranchesCollection
from serum.services.mongo_collections.v1.users_collection import UsersCollection
from serum.services_initializer import init_services


@pytest.mark.asyncio
async def test_branch_creation_restricted_to_root():
    load_dotenv("app/.env")
    await init_services()

    # Limpiar colecciones relevantes
    await BranchesCollection.get_instance()._collection.delete_many({})
    await UsersCollection.get_instance()._collection.delete_many({})

    # 1. Asegurar usuario root y usuario común
    root_user = await create_root_user()
    users_repo = UsersRepository.get_instance()
    regular_user = await users_repo.create_user(
        CreateUser(
            username="operador_regular",
            password="password123",
            name="Operador Regular",
            role="Operador",
            accessLevel=3,
        )
    )

    token_root = TokenManager.create_session_token(
        user_id=root_user.id,
        username=root_user.username,
        role=root_user.role,
    )
    token_regular = TokenManager.create_session_token(
        user_id=regular_user.id,
        username=regular_user.username,
        role=regular_user.role,
    )

    branch_payload = {
        "name": "Sucursal Norte",
        "address": "Av. Independencia 456",
        "phone": "555-9876",
    }

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Caso A: Petición sin token -> 401 Unauthorized
        res_unauth = await client.post(
            "/api/v1/branches",
            json=branch_payload,
            headers={"X-Servin": "SerumDB"},
        )
        assert res_unauth.status_code == 401

        # Caso B: Petición con usuario no root -> 403 Forbidden
        res_regular = await client.post(
            "/api/v1/branches",
            json=branch_payload,
            headers={
                "Authorization": f"Bearer {token_regular}",
                "X-Servin": "SerumDB",
            },
        )
        assert res_regular.status_code == 403
        assert "Solo el usuario root" in res_regular.json().get("detail", "")

        # Caso C: Petición con usuario root -> 200 OK
        res_root = await client.post(
            "/api/v1/branches",
            json=branch_payload,
            headers={
                "Authorization": f"Bearer {token_root}",
                "X-Servin": "SerumDB",
            },
        )
        assert res_root.status_code == 200
        created = res_root.json()
        assert created["name"] == "Sucursal Norte"
        assert "id" in created
