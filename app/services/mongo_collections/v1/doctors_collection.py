from typing import Any

from pymongo import ReturnDocument
from services import BaseMongoCollection


class DoctorsCollection(BaseMongoCollection):
    collection_name = "Doctors"

    async def create_doctor(self, doctor: dict) -> None:
        collection = self._collection
        await collection.insert_one(doctor)

    async def fetch_all_doctors(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_doctor_by_id(self, doctor_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": doctor_id})
        return result

    async def update_doctor_by_id(
        self,
        doctor_id: str,
        doctor: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": doctor_id},
            {"$set": doctor},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_doctor_by_id(self, doctor_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": doctor_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
