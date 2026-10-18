import pytest
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient

from main import app
from serum.services_initializer import init_services
from serum.repos.v1.app_settings import (
    AppSettingsRepository,
)
from serum.services.mongo_collections.v1.app_settings_collection import (
    AppSettingsCollection,
)
from serum.tools.app_settings_tool import AppSettingsTool


@pytest.mark.asyncio
async def test_app_settings_lifecycle_and_endpoints():
    load_dotenv("app/.env")
    from serum.services.mongo_service import MongoService

    await MongoService().init_service()

    # 1. Limpiar colección de configuraciones para probar inicialización limpia
    await AppSettingsCollection.get_instance()._collection.delete_many({})

    # 2. Inicializar servicios (crea Default con valores en False)
    await init_services()

    # 3. Validar valores por defecto en repositorio
    repo = AppSettingsRepository.get_instance()
    current = await repo.get_current_app_settings()
    assert current.id == "Default"
    assert current.useCost is False
    assert current.usePrice2 is False
    assert current.allowEditPrice is False
    assert current.createdAt > 0

    # 4. Validar que AppSettingsTool en memoria tiene los mismos valores
    tool = AppSettingsTool()
    tool_settings = await tool.get_current_app_settings()
    assert tool_settings.id == "Default"
    assert tool_settings.useCost is False
    assert tool_settings.usePrice2 is False
    assert tool_settings.allowEditPrice is False

    # 5. Probar endpoints REST con AsyncClient
    transport = ASGITransport(app=app)
    headers = {"X-Servin": "SerumDB"}
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=headers
    ) as ac:
        # GET /api/v1/app-settings/current
        res_current = await ac.get("/api/v1/app-settings/current")
        assert res_current.status_code == 200
        data = res_current.json()
        assert data["id"] == "Default"
        assert data["useCost"] is False
        assert data["usePrice2"] is False
        assert data["allowEditPrice"] is False

        # PATCH /api/v1/app-settings/Default
        patch_body = {
            "useCost": True,
            "usePrice2": True,
            "allowEditPrice": True,
        }
        res_patch = await ac.patch("/api/v1/app-settings/Default", json=patch_body)
        assert res_patch.status_code == 200
        patched = res_patch.json()
        assert patched["useCost"] is True
        assert patched["usePrice2"] is True
        assert patched["allowEditPrice"] is True
        assert patched["updatedAt"] is not None

        # Verificar que el caché en AppSettingsTool se refrescó
        cached_after_patch = await tool.get_current_app_settings()
        assert cached_after_patch.useCost is True
        assert cached_after_patch.usePrice2 is True
        assert cached_after_patch.allowEditPrice is True

        # Restablecer a False y verificar
        res_reset = await ac.patch(
            "/api/v1/app-settings/Default",
            json={"useCost": False, "usePrice2": False, "allowEditPrice": False},
        )
        assert res_reset.status_code == 200
        reset_data = res_reset.json()
        assert reset_data["useCost"] is False
        assert reset_data["usePrice2"] is False
        assert reset_data["allowEditPrice"] is False
