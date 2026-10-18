from typing import Any

from serum.services.mongo_collections.v1 import LabTestsCollection


class LabTestsDataSource:
    async def create_lab_test(
        self, lab_test: dict[str, Any], session: Any = None
    ) -> dict[str, Any]:
        collection = LabTestsCollection.get_instance()
        await collection.create_lab_test(lab_test, session=session)
        return lab_test

    async def create_lab_tests_batch(
        self, lab_tests: list[dict[str, Any]], session: Any = None
    ) -> list[dict[str, Any]]:
        collection = LabTestsCollection.get_instance()
        await collection.create_lab_tests_batch(lab_tests, session=session)
        return lab_tests

    async def get_all_lab_tests(
        self, branchId: str | None = None, branch_id: str | None = None
    ) -> list[dict[str, Any]]:
        collection = LabTestsCollection.get_instance()
        return await collection.fetch_all_lab_tests(branchId=branchId or branch_id)

    async def get_lab_test_by_id(
        self, lab_test_id: str, branchId: str | None = None, branch_id: str | None = None
    ) -> dict[str, Any] | None:
        collection = LabTestsCollection.get_instance()
        return await collection.fetch_lab_test_by_id(
            lab_test_id, branchId=branchId or branch_id
        )

    async def search_lab_test_by_text(
        self, text_query: str, branchId: str | None = None, branch_id: str | None = None
    ) -> list[dict[str, Any]]:
        collection = LabTestsCollection.get_instance()
        return await collection.search_lab_test_by_text(
            text_query, branchId=branchId or branch_id
        )

    async def update_lab_test_by_id(
        self, lab_test_id: str, lab_test: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = LabTestsCollection.get_instance()
        return await collection.update_lab_test_by_id(lab_test_id, lab_test)

    async def delete_lab_test_by_id(self, lab_test_id: str) -> dict[str, Any] | None:
        collection = LabTestsCollection.get_instance()
        return await collection.delete_lab_test_by_id(lab_test_id)
