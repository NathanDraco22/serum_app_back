from typing import Any
from serum.services.mongo_collections.v1.roles_collection import RolesCollection


class RolesDataSource:

    async def create_role(self, role: dict[str, Any]) -> dict[str, Any]:
        collection = RolesCollection.get_instance()
        await collection.create_role(role)
        return role

    async def get_all_roles(self) -> list[dict[str, Any]]:
        collection = RolesCollection.get_instance()
        return await collection.fetch_all_roles()

    async def get_role_by_id(self, role_id: str) -> dict[str, Any] | None:
        collection = RolesCollection.get_instance()
        return await collection.fetch_role_by_id(role_id)

    async def get_role_by_name(self, name: str) -> dict[str, Any] | None:
        collection = RolesCollection.get_instance()
        return await collection.fetch_role_by_name(name)

    async def update_role_by_id(
        self, role_id: str, role: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = RolesCollection.get_instance()
        return await collection.update_role_by_id(role_id, role)

    async def delete_role_by_id(self, role_id: str) -> dict[str, Any] | None:
        collection = RolesCollection.get_instance()
        return await collection.delete_role_by_id(role_id)
