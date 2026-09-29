from typing import Any

from pymongo import ReturnDocument

from services import BaseMongoCollection


class BranchesCollection(BaseMongoCollection):
    collection_name = "Branches"

    async def create_branch(self, branch: dict) -> None:
        collection = self._collection
        await collection.insert_one(branch)

    async def create_branch_if_absent(self, branch_id: str, branch: dict) -> None:
        collection = self._collection
        await collection.update_one(
            {"id": branch_id},
            {"$setOnInsert": branch},
            upsert=True,
        )

    async def fetch_all_branches(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_branch_by_id(self, branch_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": branch_id})
        return result

    async def update_branch_by_id(
        self,
        branch_id: str,
        branch: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": branch_id},
            {"$set": branch},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_branch_by_id(self, branch_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": branch_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
