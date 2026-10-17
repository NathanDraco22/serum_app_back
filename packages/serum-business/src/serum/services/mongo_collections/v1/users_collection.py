from typing import Any

from pymongo import ReturnDocument

from serum.services.base_mongo_collection import BaseMongoCollection


class UsersCollection(BaseMongoCollection):
    collection_name = "Users"

    async def create_user(self, user: dict) -> None:
        collection = self._collection
        await collection.insert_one(user)

    async def create_user_if_absent(self, user_id: str, user: dict) -> None:
        collection = self._collection
        await collection.update_one(
            {"id": user_id},
            {"$setOnInsert": user},
            upsert=True,
        )

    async def fetch_all_users(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({
            "isDeleted": {"$ne": True},
            "isInternal": {"$ne": True},
        })

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"id": user_id, "isDeleted": {"$ne": True}}
        )
        return result

    async def update_user_by_id(
        self,
        user_id: str,
        user: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": user_id, "isDeleted": {"$ne": True}},
            {"$set": user},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def fetch_user_by_username(
        self, username: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one(
            {"username": username, "isDeleted": {"$ne": True}}
        )

    async def fetch_user_by_email(self, email: str) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one(
            {"email": email, "isDeleted": {"$ne": True}}
        )

    async def fetch_user_by_phone(self, phone: str) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one(
            {"phone": phone, "isDeleted": {"$ne": True}}
        )

    async def delete_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": user_id, "isDeleted": {"$ne": True}},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
