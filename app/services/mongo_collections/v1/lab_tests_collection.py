import re
from typing import Any

from pymongo import ReturnDocument, IndexModel

from services import BaseMongoCollection


class LabTestsCollection(BaseMongoCollection):
    collection_name = "LabTests"

    async def create_lab_test(self, lab_test: dict) -> None:
        collection = self._collection
        await collection.insert_one(lab_test)

    async def fetch_all_lab_tests(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({"isDeleted": False})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_lab_test_by_id(self, lab_test_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": lab_test_id, "isDeleted": False})
        return result

    async def search_lab_test_by_text(self, text_query: str) -> list[dict[str, Any]]:
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
                                    "input": "$parameterName",
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
            {"$sort": {"finalScore": -1, "parameterName": 1}},
            {"$limit": 20},
            {"$project": {"baseScore": 0, "positionBoost": 0, "finalScore": 0}},
        ]
        cursor = await collection.aggregate(pipeline)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def update_lab_test_by_id(
        self,
        lab_test_id: str,
        lab_test: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": lab_test_id, "isDeleted": False},
            {"$set": lab_test},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_lab_test_by_id(self, lab_test_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": lab_test_id, "isDeleted": False},
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
                        ("parameterName", "text"),
                        ("searchPrefixes", "text"),
                        ("medicalClassification", "text"),
                        ("id", "text"),
                    ],
                    weights={
                        "parameterName": 10,
                        "searchPrefixes": 5,
                        "medicalClassification": 3,
                        "id": 1,
                    },
                    name="TextSearchIndex",
                ),
            ]
        )
