from typing import Any

from serum.services.mongo_collections.v1.app_settings_collection import (
    AppSettingsCollection,
)


class AppSettingsDataSource:
    async def create_app_setting(self, app_setting: dict[str, Any]) -> dict[str, Any]:
        collection = AppSettingsCollection.get_instance()
        await collection.create_app_setting(app_setting)
        return app_setting

    async def create_app_setting_if_absent(
        self, app_setting: dict[str, Any]
    ) -> dict[str, Any]:
        collection = AppSettingsCollection.get_instance()
        await collection.create_app_setting_if_absent(app_setting)
        return app_setting

    async def get_all_app_settings(self) -> list[dict[str, Any]]:
        collection = AppSettingsCollection.get_instance()
        return await collection.fetch_all_app_settings()

    async def get_app_setting_by_id(self, app_setting_id: str) -> dict[str, Any] | None:
        collection = AppSettingsCollection.get_instance()
        return await collection.fetch_app_setting_by_id(app_setting_id)

    async def update_app_setting_by_id(
        self, app_setting_id: str, app_setting: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = AppSettingsCollection.get_instance()
        return await collection.update_app_setting_by_id(app_setting_id, app_setting)

    async def delete_app_setting_by_id(
        self, app_setting_id: str
    ) -> dict[str, Any] | None:
        collection = AppSettingsCollection.get_instance()
        return await collection.delete_app_setting_by_id(app_setting_id)
