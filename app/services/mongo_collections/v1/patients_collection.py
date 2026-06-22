from typing import Any

from pymongo import ReturnDocument
from services import BaseMongoCollection


class PatientsCollection(BaseMongoCollection):
    collection_name = "Patients"

    async def create_patient(self, patient: dict) -> None:
        collection = self._collection
        await collection.insert_one(patient)

    async def fetch_all_patients(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_patient_by_id(self, patient_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": patient_id})
        return result

    async def update_patient_by_id(
        self,
        patient_id: str,
        patient: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": patient_id},
            {"$set": patient},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_patient_by_id(self, patient_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": patient_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
