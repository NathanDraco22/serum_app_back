import re
from typing import Any

from pymongo import ReturnDocument, IndexModel

from services import BaseMongoCollection


class ExamsCollection(BaseMongoCollection):
    collection_name = "Exams"

    async def create_exam(self, exam: dict) -> None:
        collection = self._collection
        await collection.insert_one(exam)

    async def fetch_all_exams(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({"isDeleted": False})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_exam_by_id(self, exam_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": exam_id, "isDeleted": False})
        return result

    async def search_exam_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = self._collection
        safe_query = re.escape(text_query)

        pipeline = [
            {
                "$match": {
                    "$text": {
                        "$search": safe_query,
                        "$caseSensitive": False,
                        "$diacriticSensitive": False,
                    },
                    "isDeleted": False,
                }
            },
            {
                "$addFields": {
                    "baseScore": {"$meta": "textScore"},
                    "positionBoost": {
                        "$cond": [
                            {
                                "$regexMatch": {
                                    "input": "$name",
                                    "regex": f"^{safe_query}",
                                    "options": "i",
                                }
                            },
                            100,
                            0,
                        ]
                    },
                }
            },
            {"$addFields": {"finalScore": {"$add": ["$baseScore", "$positionBoost"]}}},
            {"$sort": {"finalScore": -1, "name": 1}},
            {"$limit": 20},
            {"$project": {"baseScore": 0, "positionBoost": 0, "finalScore": 0}},
        ]
        cursor = await collection.aggregate(pipeline)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def update_exam_by_id(
        self,
        exam_id: str,
        exam: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": exam_id, "isDeleted": False},
            {"$set": exam},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_exam_by_id(self, exam_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": exam_id, "isDeleted": False},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel(
                    [
                        ("id", 1),
                        ("isDeleted", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("name", "text"),
                        ("searchPrefixes", "text"),
                        ("commercialCategory", "text"),
                        ("id", "text"),
                    ],
                    weights={
                        "name": 10,
                        "searchPrefixes": 5,
                        "commercialCategory": 3,
                        "id": 1,
                    },
                    name="TextSearchIndex",
                ),
            ]
        )
