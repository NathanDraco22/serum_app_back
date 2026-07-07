from typing import Any

from services.mongo_collections.v1 import LabTestsCollection


class LabTestsDataSource:
    async def create_lab_test(self, lab_test: dict[str, Any]) -> dict[str, Any]:
        collection = LabTestsCollection.get_instance()
        await collection.create_lab_test(lab_test)
        return lab_test

    async def get_all_lab_tests(self) -> list[dict[str, Any]]:
        collection = LabTestsCollection.get_instance()
        return await collection.fetch_all_lab_tests()

    async def get_lab_test_by_id(self, lab_test_id: str) -> dict[str, Any] | None:
        collection = LabTestsCollection.get_instance()
        return await collection.fetch_lab_test_by_id(lab_test_id)

    async def update_lab_test_by_id(
        self, lab_test_id: str, lab_test: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = LabTestsCollection.get_instance()
        return await collection.update_lab_test_by_id(lab_test_id, lab_test)

    async def delete_lab_test_by_id(self, lab_test_id: str) -> dict[str, Any] | None:
        collection = LabTestsCollection.get_instance()
        return await collection.delete_lab_test_by_id(lab_test_id)
