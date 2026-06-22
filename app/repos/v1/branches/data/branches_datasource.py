from typing import Any
from services.mongo_collections.v1 import BranchesCollection


class BranchesDataSource:

    async def create_branch(self, branch: dict[str, Any]) -> dict[str, Any]:
        collection = BranchesCollection.get_instance()
        await collection.create_branch(branch)
        return branch

    async def get_all_branches(self) -> list[dict[str, Any]]:
        collection = BranchesCollection.get_instance()
        return await collection.fetch_all_branches()

    async def get_branch_by_id(self, branch_id: str) -> dict[str, Any] | None:
        collection = BranchesCollection.get_instance()
        return await collection.fetch_branch_by_id(branch_id)

    async def update_branch_by_id(
        self, branch_id: str, branch: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = BranchesCollection.get_instance()
        return await collection.update_branch_by_id(branch_id, branch)

    async def delete_branch_by_id(self, branch_id: str) -> dict[str, Any] | None:
        collection = BranchesCollection.get_instance()
        return await collection.delete_branch_by_id(branch_id)
