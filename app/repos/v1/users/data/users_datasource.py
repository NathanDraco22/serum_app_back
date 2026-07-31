from typing import Any

from services.mongo_collections.v1 import UsersCollection


class UsersDataSource:
    async def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        collection = UsersCollection.get_instance()
        await collection.create_user(user)
        return user

    async def get_all_users(self) -> list[dict[str, Any]]:
        collection = UsersCollection.get_instance()
        return await collection.fetch_all_users()

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = UsersCollection.get_instance()
        return await collection.fetch_user_by_id(user_id)

    async def update_user_by_id(
        self, user_id: str, user: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = UsersCollection.get_instance()
        return await collection.update_user_by_id(user_id, user)

    async def get_user_by_username(
        self, username: str
    ) -> dict[str, Any] | None:
        collection = UsersCollection.get_instance()
        return await collection.fetch_user_by_username(username)

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        collection = UsersCollection.get_instance()
        return await collection.fetch_user_by_email(email)

    async def get_user_by_phone(self, phone: str) -> dict[str, Any] | None:
        collection = UsersCollection.get_instance()
        return await collection.fetch_user_by_phone(phone)

    async def delete_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = UsersCollection.get_instance()
        return await collection.delete_user_by_id(user_id)
