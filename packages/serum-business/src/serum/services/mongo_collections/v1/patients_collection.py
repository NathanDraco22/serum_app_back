import re
from typing import Any

from pymongo import ReturnDocument, IndexModel
from pymongo.errors import OperationFailure

from serum.services import BaseMongoCollection



class PatientsCollection(BaseMongoCollection):
    collection_name = "Patients"

    async def create_patient(self, patient: dict) -> None:
        collection = self._collection
        await collection.insert_one(patient)

    async def fetch_all_patients(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({"isDeleted": False})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_patient_by_id(self, patient_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": patient_id, "isDeleted": False})
        return result

    async def get_patient_by_card_id(self, card_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"cardId": card_id, "isDeleted": False})
        return result

    async def search_patient_by_text(self, text_query: str) -> list[dict[str, Any]]:
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

    async def update_patient_by_id(
        self,
        patient_id: str,
        patient: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": patient_id, "isDeleted": False},
            {"$set": patient},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_patient_by_id(self, patient_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": patient_id, "isDeleted": False},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def create_indexes(self):
        collection = self._collection
        indexes = [
            IndexModel(
                [
                    ("id", 1),
                ],
                unique=True,
            ),
            IndexModel(
                [
                    ("name", "text"),
                    ("searchPrefixes", "text"),
                    ("cardId", "text"),
                    ("phone", "text"),
                    ("id", "text"),
                ],
                weights={
                    "name": 10,
                    "searchPrefixes": 5,
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
        try:
            await collection.create_indexes(indexes)
        except OperationFailure as e:
            if e.code in (85, 86):
                try:
                    await collection.drop_index("TextSearchIndex")
                except Exception:
                    pass
                await collection.create_indexes(indexes)
            else:
                raise

