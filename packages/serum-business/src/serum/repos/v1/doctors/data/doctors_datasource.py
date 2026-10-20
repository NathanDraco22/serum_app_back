from typing import Any

from serum.services.mongo_collections.v1 import DoctorsCollection


class DoctorsDataSource:
    async def create_doctor(self, doctor: dict[str, Any]) -> dict[str, Any]:
        collection = DoctorsCollection.get_instance()
        await collection.create_doctor(doctor)
        return doctor

    async def get_all_doctors(
        self, origin_branch: str | None = None
    ) -> list[dict[str, Any]]:
        collection = DoctorsCollection.get_instance()
        return await collection.fetch_all_doctors(origin_branch=origin_branch)

    async def get_doctor_by_id(self, doctor_id: str) -> dict[str, Any] | None:
        collection = DoctorsCollection.get_instance()
        return await collection.fetch_doctor_by_id(doctor_id)

    async def get_doctor_by_card_id(self, card_id: str) -> dict[str, Any] | None:
        collection = DoctorsCollection.get_instance()
        return await collection.get_doctor_by_card_id(card_id)

    async def search_doctor_by_text(
        self, text_query: str, origin_branch: str | None = None
    ) -> list[dict[str, Any]]:
        collection = DoctorsCollection.get_instance()
        return await collection.search_doctor_by_text(
            text_query, origin_branch=origin_branch
        )

    async def update_doctor_by_id(
        self, doctor_id: str, doctor: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = DoctorsCollection.get_instance()
        return await collection.update_doctor_by_id(doctor_id, doctor)

    async def delete_doctor_by_id(self, doctor_id: str) -> dict[str, Any] | None:
        collection = DoctorsCollection.get_instance()
        return await collection.delete_doctor_by_id(doctor_id)
