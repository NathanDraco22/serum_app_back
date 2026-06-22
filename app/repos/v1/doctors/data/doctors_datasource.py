from typing import Any
from services.mongo_collections.v1 import DoctorsCollection


class DoctorsDataSource:

    async def create_doctor(self, doctor: dict[str, Any]) -> dict[str, Any]:
        collection = DoctorsCollection.get_instance()
        await collection.create_doctor(doctor)
        return doctor

    async def get_all_doctors(self) -> list[dict[str, Any]]:
        collection = DoctorsCollection.get_instance()
        return await collection.fetch_all_doctors()

    async def get_doctor_by_id(self, doctor_id: str) -> dict[str, Any] | None:
        collection = DoctorsCollection.get_instance()
        return await collection.fetch_doctor_by_id(doctor_id)

    async def update_doctor_by_id(
        self, doctor_id: str, doctor: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = DoctorsCollection.get_instance()
        return await collection.update_doctor_by_id(doctor_id, doctor)

    async def delete_doctor_by_id(self, doctor_id: str) -> dict[str, Any] | None:
        collection = DoctorsCollection.get_instance()
        return await collection.delete_doctor_by_id(doctor_id)
