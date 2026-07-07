from typing import Any

from pymongo import ReturnDocument

from services import BaseMongoCollection


class ExamsCollection(BaseMongoCollection):
    collection_name = "Exams"

    async def create_exam(self, exam: dict) -> None:
        collection = self._collection
        await collection.insert_one(exam)

    async def fetch_all_exams(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_exam_by_id(self, exam_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": exam_id})
        return result

    async def update_exam_by_id(
        self,
        exam_id: str,
        exam: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": exam_id},
            {"$set": exam},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_exam_by_id(self, exam_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": exam_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
