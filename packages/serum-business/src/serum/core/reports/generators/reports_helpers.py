from typing import Any

from serum.services.mongo_collections.v1 import BranchesCollection, UsersCollection


def _branch_display_name(branch: dict[str, Any]) -> str:
    name = branch.get("name") or "Sucursal"
    city = (branch.get("city") or "").strip()
    if not city or city.lower() in name.lower():
        return name
    return f"{name} - {city}"


async def get_branches_map() -> dict[str, str]:
    branches_col = BranchesCollection.get_instance()._collection
    cursor = branches_col.find(
        {"isDeleted": {"$ne": True}}, {"id": 1, "name": 1, "city": 1}
    )
    branches = await cursor.to_list(length=None)
    await cursor.close()
    return {b["id"]: _branch_display_name(b) for b in branches}


async def get_users_map() -> dict[str, str]:
    users_col = UsersCollection.get_instance()._collection
    cursor = users_col.find(
        {"isDeleted": {"$ne": True}},
        {"id": 1, "fullName": 1, "username": 1},
    )
    users = await cursor.to_list(length=None)
    await cursor.close()
    return {
        u["id"]: u.get("fullName") or u.get("username", "Usuario")
        for u in users
    }
