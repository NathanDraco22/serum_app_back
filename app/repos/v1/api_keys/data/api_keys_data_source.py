from typing import Any

from services.mongo_collections.v1.api_keys_collection import ApiKeysCollection


class ApiKeysDataSource:
    async def create_api_key(self, api_key_dict: dict[str, Any]) -> None:
        collection = ApiKeysCollection.get_instance()
        await collection.create_api_key(api_key_dict)

    async def get_all_api_keys(self) -> list[dict[str, Any]]:
        collection = ApiKeysCollection.get_instance()
        return await collection.fetch_all_api_keys()

    async def get_api_key_by_id(self, key_id: str) -> dict[str, Any] | None:
        collection = ApiKeysCollection.get_instance()
        return await collection.fetch_api_key_by_id(key_id)

    async def get_api_key_by_value(self, key_value: str) -> dict[str, Any] | None:
        collection = ApiKeysCollection.get_instance()
        return await collection.fetch_api_key_by_value(key_value)

    async def toggle_api_key_status(
        self, key_id: str, is_active: bool, updated_at: int
    ) -> dict[str, Any] | None:
        collection = ApiKeysCollection.get_instance()
        return await collection.toggle_api_key_status(key_id, is_active, updated_at)

    async def update_last_used_at(self, key_id: str, timestamp: int) -> None:
        collection = ApiKeysCollection.get_instance()
        await collection.update_last_used_at(key_id, timestamp)

    async def delete_api_key_by_id(
        self, key_id: str, updated_at: int
    ) -> dict[str, Any] | None:
        collection = ApiKeysCollection.get_instance()
        return await collection.delete_api_key_by_id(key_id, updated_at)
