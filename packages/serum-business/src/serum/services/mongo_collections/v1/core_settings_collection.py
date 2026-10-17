from typing import Any

from pymongo import ReturnDocument

from serum.services import BaseMongoCollection


class CoreSettingsCollection(BaseMongoCollection):
    collection_name = "CoreSettings"

    async def create_core_setting(self, core_setting: dict) -> None:
        collection = self._collection
        await collection.insert_one(core_setting)

    async def fetch_all_core_settings(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def fetch_core_setting_by_id(
        self, core_setting_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": core_setting_id})
        return result

    async def fetch_core_setting_by_nickname(
        self, nickname: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"nickname": nickname})
        return result

    async def update_core_setting_by_nickname(
        self,
        nickname: str,
        core_setting: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"nickname": nickname},
            {"$set": core_setting},
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def update_core_setting_by_id(
        self,
        core_setting_id: str,
        core_setting: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": core_setting_id},
            {"$set": core_setting},
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def delete_core_setting_by_id(
        self, core_setting_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": core_setting_id})
        return result
