import httpx
import pytest
from dotenv import load_dotenv

from main import app
from serum.core.default_values.create_root_user import create_root_user
from serum.core.security import TokenManager
from serum.repos.v1.users import (
    CreateUser,
    LastAdminError,
    UpdateUser,
    UsersRepository,
)
from serum.services.mongo_collections.v1.cash_shifts_collection import (
    CashShiftsCollection,
)
from serum.services.mongo_collections.v1.users_collection import UsersCollection
from serum.services_initializer import init_services
from serum.tools.time_tools import TimeTools


@pytest.mark.asyncio
async def test_users_admin_guards_and_editing():
    load_dotenv("app/.env")
    await init_services()

    users_col = UsersCollection.get_instance()._collection
    shifts_col = CashShiftsCollection.get_instance()._collection
    await users_col.delete_many({})
    await shifts_col.delete_many({})

    root_user = await create_root_user()
    users_repo = UsersRepository.get_instance()

    admin = await users_repo.create_user(
        CreateUser(
            username="admin_test",
            password="password123",
            name="Admin Test",
            role="Admin",
            accessLevel=5,
            email="admin@test.com",
        )
    )
    supervisor = await users_repo.create_user(
        CreateUser(
            username="supervisor_test",
            password="password123",
            name="Supervisor Test",
            role="Supervisor",
            accessLevel=4,
            email="supervisor@test.com",
        )
    )
    await users_repo.create_user(
        CreateUser(
            username="duplicate_test",
            password="password123",
            name="Duplicate Test",
            role="Operador",
            accessLevel=3,
            email="duplicate@test.com",
        )
    )

    token_root = TokenManager.create_session_token(
        user_id=root_user.id,
        username=root_user.username,
        role=root_user.role,
    )
    token_admin = TokenManager.create_session_token(
        user_id=admin.id,
        username=admin.username,
        role=admin.role,
    )
    token_supervisor = TokenManager.create_session_token(
        user_id=supervisor.id,
        username=supervisor.username,
        role=supervisor.role,
    )

    def headers(token: str | None = None) -> dict[str, str]:
        result = {"X-Servin": "SerumDB"}
        if token:
            result["Authorization"] = f"Bearer {token}"
        return result

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Sin token -> 401
        res = await client.patch(
            f"/api/v1/users/{supervisor.id}",
            json={"name": "Sin autorización"},
            headers=headers(),
        )
        assert res.status_code == 401

        # Supervisor nivel 4 -> 403
        res = await client.patch(
            f"/api/v1/users/{supervisor.id}",
            json={"name": "Supervisor no autorizado"},
            headers=headers(token_supervisor),
        )
        assert res.status_code == 403

        # Admin -> 200 y edición efectiva
        res = await client.patch(
            f"/api/v1/users/{supervisor.id}",
            json={"name": "Supervisor Editado"},
            headers=headers(token_admin),
        )
        assert res.status_code == 200
        assert res.json()["name"] == "Supervisor Editado"
        assert res.json()["password"] == ""

        # Duplicado de email -> 409
        res = await client.patch(
            f"/api/v1/users/{supervisor.id}",
            json={"email": "duplicate@test.com"},
            headers=headers(token_admin),
        )
        assert res.status_code == 409

        # Admin no puede desactivarse a sí mismo -> 403
        res = await client.patch(
            f"/api/v1/users/{admin.id}",
            json={"isActive": False},
            headers=headers(token_admin),
        )
        assert res.status_code == 403

        # Admin no puede quitarse su propio rol -> 403
        res = await client.patch(
            f"/api/v1/users/{admin.id}",
            json={"role": "Operador", "accessLevel": 3},
            headers=headers(token_admin),
        )
        assert res.status_code == 403

        # El usuario root está protegido -> 403
        res = await client.patch(
            f"/api/v1/users/{root_user.id}",
            json={"name": "Root no editable"},
            headers=headers(token_admin),
        )
        assert res.status_code == 403

        # El directorio sigue disponible para usuarios autenticados -> 200
        res = await client.get(
            "/api/v1/users",
            headers=headers(token_supervisor),
        )
        assert res.status_code == 200
        assert all(
            user["password"] == "" for user in res.json()["data"]
        )

        # Supervisor no puede crear usuarios -> 403
        res = await client.post(
            "/api/v1/users",
            json={
                "username": "created_by_supervisor",
                "password": "password123",
                "name": "Created by Supervisor",
                "role": "Operador",
                "accessLevel": 3,
            },
            headers=headers(token_supervisor),
        )
        assert res.status_code == 403

        # Admin sí puede crear usuarios -> 200
        res = await client.post(
            "/api/v1/users",
            json={
                "username": "created_by_admin",
                "password": "password123",
                "name": "Created by Admin",
                "role": "Operador",
                "accessLevel": 3,
            },
            headers=headers(token_admin),
        )
        assert res.status_code == 200
        assert res.json()["password"] == ""

        # No se puede desactivar a un usuario con turno de caja abierto -> 409
        now = TimeTools.get_now_in_milliseconds()
        await shifts_col.insert_one(
            {
                "id": "test_shift_guard",
                "userId": supervisor.id,
                "branchId": "ORIGIN_BRANCH",
                "notes": "",
                "userName": supervisor.name,
                "branchName": "Origen",
                "status": "OPEN",
                "openedAt": now,
                "closedAt": None,
                "initialBalance": 0,
                "cashBalance": 0,
                "cardBalance": 0,
                "transferBalance": 0,
                "bankTransfers": {},
                "totalBalance": 0,
                "declaredCash": None,
                "difference": None,
                "isDeleted": False,
                "createdAt": now,
                "updatedAt": None,
            }
        )
        res = await client.patch(
            f"/api/v1/users/{supervisor.id}",
            json={"isActive": False},
            headers=headers(token_admin),
        )
        assert res.status_code == 409
        await shifts_col.delete_many({})

        # Root tampoco puede eliminarse -> 403
        res = await client.delete(
            f"/api/v1/users/{root_user.id}",
            headers=headers(token_root),
        )
        assert res.status_code == 403

        # Admin no puede eliminarse a sí mismo -> 403
        res = await client.delete(
            f"/api/v1/users/{admin.id}",
            headers=headers(token_admin),
        )
        assert res.status_code == 403

    # Guard de último administrador a nivel de repositorio.
    await users_col.delete_one({"id": root_user.id})
    with pytest.raises(LastAdminError):
        await users_repo.update_user_by_id(
            admin.id,
            UpdateUser(isActive=False),
            actor_id=None,
        )

    await users_col.delete_many({})
    await shifts_col.delete_many({})
