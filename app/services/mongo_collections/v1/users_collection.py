from typing import Any

from pymongo import ReturnDocument

from services import BaseMongoCollection


class UsersCollection(BaseMongoCollection):
    collection_name = "Users"

    async def create_user(self, user: dict) -> None:
        collection = self._collection
        await collection.insert_one(user)

    async def fetch_all_users(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": user_id})
        return result

    async def update_user_by_id(
        self,
        user_id: str,
        user: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": user_id},
            {"$set": user},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": user_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
