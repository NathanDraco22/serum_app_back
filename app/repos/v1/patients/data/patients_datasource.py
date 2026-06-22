from typing import Any
from services.mongo_collections.v1 import PatientsCollection


class PatientsDataSource:

    async def create_patient(self, patient: dict[str, Any]) -> dict[str, Any]:
        collection = PatientsCollection.get_instance()
        await collection.create_patient(patient)
        return patient

    async def get_all_patients(self) -> list[dict[str, Any]]:
        collection = PatientsCollection.get_instance()
        return await collection.fetch_all_patients()

    async def get_patient_by_id(self, patient_id: str) -> dict[str, Any] | None:
        collection = PatientsCollection.get_instance()
        return await collection.fetch_patient_by_id(patient_id)

    async def update_patient_by_id(
        self, patient_id: str, patient: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = PatientsCollection.get_instance()
        return await collection.update_patient_by_id(patient_id, patient)

    async def delete_patient_by_id(self, patient_id: str) -> dict[str, Any] | None:
        collection = PatientsCollection.get_instance()
        return await collection.delete_patient_by_id(patient_id)
