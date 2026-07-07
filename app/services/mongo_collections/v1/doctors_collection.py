import re
from typing import Any

from pymongo import ReturnDocument, IndexModel

from services import BaseMongoCollection


class DoctorsCollection(BaseMongoCollection):
    collection_name = "Doctors"

    async def create_doctor(self, doctor: dict) -> None:
        collection = self._collection
        await collection.insert_one(doctor)

    async def fetch_all_doctors(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({"isDeleted": False})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_doctor_by_id(self, doctor_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": doctor_id, "isDeleted": False})
        return result

    async def get_doctor_by_card_id(self, card_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"cardId": card_id, "isDeleted": False})
        return result

    async def search_doctor_by_text(self, text_query: str) -> list[dict[str, Any]]:
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

    async def update_doctor_by_id(
        self,
        doctor_id: str,
        doctor: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": doctor_id, "isDeleted": False},
            {"$set": doctor},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_doctor_by_id(self, doctor_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": doctor_id, "isDeleted": False},
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
                        ("specialty", "text"),
                        ("cardId", "text"),
                        ("phone", "text"),
                        ("id", "text"),
                    ],
                    weights={
                        "name": 10,
                        "searchPrefixes": 5,
                        "specialty": 3,
                        "cardId": 1,
                        "phone": 1,
                        "id": 1,
                    },
                    name="TextSearchIndex",
                ),
                IndexModel(
                    [
                        ("cardId", 1),
                    ],
                ),
            ]
        )
