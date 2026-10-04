from services.mongo_collections.v1 import BranchesCollection, UsersCollection


async def get_branches_map() -> dict[str, str]:
    branches_col = BranchesCollection.get_instance()._collection
    cursor = branches_col.find(
        {"isDeleted": {"$ne": True}}, {"id": 1, "name": 1}
    )
    branches = await cursor.to_list(length=None)
    await cursor.close()
    return {b["id"]: b.get("name", "Sucursal") for b in branches}


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
