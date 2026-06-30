from typing import Any

from pymongo import ReturnDocument
from services import BaseMongoCollection


class LabTestsCollection(BaseMongoCollection):
    collection_name = "LabTests"

    async def create_lab_test(self, lab_test: dict) -> None:
        collection = self._collection
        await collection.insert_one(lab_test)

    async def fetch_all_lab_tests(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_lab_test_by_id(self, lab_test_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": lab_test_id})
        return result

    async def update_lab_test_by_id(
        self,
        lab_test_id: str,
        lab_test: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": lab_test_id},
            {"$set": lab_test},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_lab_test_by_id(self, lab_test_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": lab_test_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
