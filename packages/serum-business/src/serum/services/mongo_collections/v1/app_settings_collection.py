from typing import Any

from pymongo import ReturnDocument
from serum.services import BaseMongoCollection


class AppSettingsCollection(BaseMongoCollection):
    collection_name = "AppSettings"

    async def create_app_setting(self, app_setting: dict) -> None:
        collection = self._collection
        await collection.insert_one(app_setting)

    async def create_app_setting_if_absent(self, app_setting: dict) -> None:
        collection = self._collection
        await collection.find_one_and_update(
            {"id": app_setting["id"]},
            {"$setOnInsert": app_setting},
            upsert=True,
        )

    async def fetch_all_app_settings(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def fetch_app_setting_by_id(
        self, app_setting_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": app_setting_id})
        return result

    async def update_app_setting_by_id(
        self,
        app_setting_id: str,
        app_setting: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": app_setting_id},
            {"$set": app_setting},
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def delete_app_setting_by_id(
        self, app_setting_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": app_setting_id})
        return result
