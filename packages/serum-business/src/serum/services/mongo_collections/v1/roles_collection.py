from typing import Any

from pymongo import ReturnDocument

from serum.services.base_mongo_collection import BaseMongoCollection


class RolesCollection(BaseMongoCollection):
    collection_name = "Roles"

    async def create_role(self, role: dict) -> None:
        collection = self._collection
        await collection.insert_one(role)

    async def create_role_if_absent(self, role_id: str, role: dict) -> None:
        collection = self._collection
        await collection.update_one(
            {"id": role_id},
            {"$setOnInsert": role},
            upsert=True,
        )

    async def fetch_all_roles(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({"isDeleted": {"$ne": True}})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_role_by_id(self, role_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": role_id, "isDeleted": {"$ne": True}})
        return result

    async def fetch_role_by_name(self, name: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({
            "name": {"$regex": f"^{name}$", "$options": "i"},
            "isDeleted": {"$ne": True},
        })
        return result

    async def update_role_by_id(
        self,
        role_id: str,
        role: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": role_id, "isDeleted": {"$ne": True}},
            {"$set": role},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_role_by_id(self, role_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": role_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
