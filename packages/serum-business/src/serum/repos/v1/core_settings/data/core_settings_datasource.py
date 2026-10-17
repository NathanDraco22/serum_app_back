from typing import Any

from serum.services.mongo_collections.v1.core_settings_collection import (
    CoreSettingsCollection,
)


class CoreSettingsDataSource:
    async def create_core_setting(
        self, core_setting: dict[str, Any]
    ) -> dict[str, Any]:
        collection = CoreSettingsCollection.get_instance()
        await collection.create_core_setting(core_setting)
        return core_setting

    async def get_all_core_settings(self) -> list[dict[str, Any]]:
        collection = CoreSettingsCollection.get_instance()
        return await collection.fetch_all_core_settings()

    async def get_core_setting_by_id(
        self, core_setting_id: str
    ) -> dict[str, Any] | None:
        collection = CoreSettingsCollection.get_instance()
        return await collection.fetch_core_setting_by_id(core_setting_id)

    async def get_core_setting_by_nickname(
        self, nickname: str
    ) -> dict[str, Any] | None:
        collection = CoreSettingsCollection.get_instance()
        return await collection.fetch_core_setting_by_nickname(nickname)

    async def update_core_setting_by_nickname(
        self, nickname: str, core_setting: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = CoreSettingsCollection.get_instance()
        return await collection.update_core_setting_by_nickname(
            nickname, core_setting
        )

    async def update_core_setting_by_id(
        self, core_setting_id: str, core_setting: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = CoreSettingsCollection.get_instance()
        return await collection.update_core_setting_by_id(
            core_setting_id, core_setting
        )

    async def delete_core_setting_by_id(
        self, core_setting_id: str
    ) -> dict[str, Any] | None:
        collection = CoreSettingsCollection.get_instance()
        return await collection.delete_core_setting_by_id(core_setting_id)
