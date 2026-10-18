import time
from httpx import ASGITransport, AsyncClient
import jwt
import pytest

from serum.core.security import TokenManager
from serum.services_initializer import init_services
from main import app
from serum.services.mongo_collections.v1.core_settings_collection import (
    CoreSettingsCollection,
)

SERVICE_PRIVATE_KEY = b"""-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIC/59CJbQp5CtZFY5nfFGkjWdxDK0omREIeUHmObC09B
-----END PRIVATE KEY-----
"""


def encode_ed25519(payload: dict) -> str:
    return jwt.encode(payload, SERVICE_PRIVATE_KEY, algorithm="EdDSA")


def test_token_manager_super_token_verify():
    payload = {
        "sub": "test-uuid-1234",
        "origin": "Service Manager",
        "exp": int(time.time()) + 300,
    }
    token = encode_ed25519(payload)
    decoded = TokenManager.super_token_verify(token)
    assert decoded is not None
    assert decoded["sub"] == "test-uuid-1234"
    assert decoded["origin"] == "Service Manager"

    # Token con firma inválida o corrupto
    invalid_token = token[:-4] + "AAAA"
    assert TokenManager.super_token_verify(invalid_token) is None


@pytest.mark.asyncio
async def test_core_settings_activation_flow():
    await init_services()

    collection = CoreSettingsCollection.get_instance()._collection
    await collection.delete_many({})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        nickname = "lab-test-serum"
        owner_name = "Dr. Test Propietario"
        est_name = "Laboratorio Central Serum"

        content_payload = {
            "name": est_name,
            "nickname": nickname,
            "ownerName": owner_name,
            "isMultiBranch": True,
            "isUsingExpirationDate": True,
            "price": 1000,
            "isActive": True,
        }
        content_token = encode_ed25519(content_payload)

        id_payload = {
            "sub": "servin-id-999",
            "origin": "Service Manager",
            "exp": int(time.time()) + 300,
        }
        id_token = encode_ed25519(id_payload)

        # 1. Petición sin autorización -> rechazo
        res_no_auth = await client.post(
            "/api/v1/core-settings",
            headers={"X-Servin": nickname},
            json={"nickname": nickname, "token": content_token},
        )
        assert res_no_auth.status_code in (401, 403)

        # 2. Petición con autorización inválida -> rechazo 401
        res_bad_auth = await client.post(
            "/api/v1/core-settings",
            headers={"Authorization": "bad-token", "X-Servin": nickname},
            json={"nickname": nickname, "token": content_token},
        )
        assert res_bad_auth.status_code == 401

        # 3. Activación exitosa (POST /api/v1/core-settings)
        headers = {"Authorization": id_token, "X-Servin": nickname}
        body = {"nickname": nickname, "token": content_token}

        res_activate = await client.post(
            "/api/v1/core-settings",
            headers=headers,
            json=body,
        )
        assert res_activate.status_code == 200, res_activate.text
        data = res_activate.json()
        assert data["nickname"] == nickname
        assert data["name"] == est_name
        assert data["ownerName"] == owner_name
        assert data["isActive"] is True
        assert data["isMultiBranch"] is True

        # 4. Intento de reactivación (debe fallar con 400 Bad Request)
        res_duplicate = await client.post(
            "/api/v1/core-settings",
            headers=headers,
            json=body,
        )
        assert res_duplicate.status_code == 400
        assert "already exists" in res_duplicate.json()["detail"]

        # 5. Consulta de estado del Servin (GET /api/v1/auths/servin-status)
        res_status = await client.get(
            "/api/v1/auths/servin-status",
            headers={"X-Servin": nickname},
        )
        assert res_status.status_code == 200
        status_data = res_status.json()
        assert status_data["nickname"] == nickname
        assert status_data["isActive"] is True
        assert status_data["isMultiBranch"] is True

        # 6. Actualización remota vía PATCH
        update_payload = dict(content_payload)
        update_payload["isActive"] = False  # Suspender servicio remotamente
        update_token = encode_ed25519(update_payload)

        res_patch = await client.patch(
            f"/api/v1/core-settings/{nickname}",
            headers=headers,
            json={"token": update_token},
        )
        assert res_patch.status_code == 200

        # 7. Verificar que el estado refleja la suspensión
        res_status_updated = await client.get(
            "/api/v1/auths/servin-status",
            headers={"X-Servin": nickname},
        )
        assert res_status_updated.status_code == 200
        assert res_status_updated.json()["isActive"] is False

        # Limpieza final
        tenant_collection = CoreSettingsCollection.get_instance(nickname)._collection
        await tenant_collection.delete_many({})
        await collection.delete_many({})
