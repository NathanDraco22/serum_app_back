from fastapi import HTTPException, status
from core.lab_tests import LabTestsManager
from repos.v1.lab_tests import (
    CreateLabTest,
    LabTestInDb,
    LabTestsRepository,
    UpdateLabTest,
)
from responses.v1 import ListResponse


class LabTestsController:
    def __init__(self, lab_tests_repo: LabTestsRepository) -> None:
        self.lab_tests_repo = lab_tests_repo

    async def create_lab_test(self, body: CreateLabTest) -> LabTestInDb:
        return await LabTestsManager.get_instance().create_lab_test(body)

    async def get_all_lab_tests(
        self, branchId: str | None = None
    ) -> ListResponse[LabTestInDb]:
        lab_tests = await self.lab_tests_repo.get_all_lab_tests(branchId=branchId)
        return ListResponse(count=len(lab_tests), data=lab_tests)

    async def search_lab_test_by_text(
        self, text_query: str, branchId: str | None = None
    ) -> ListResponse[LabTestInDb]:
        lab_tests = await self.lab_tests_repo.search_lab_test_by_text(
            text_query, branchId=branchId
        )
        return ListResponse(count=len(lab_tests), data=lab_tests)

    async def get_lab_test_by_id(
        self, lab_test_id: str, branchId: str | None = None
    ) -> LabTestInDb:
        lab_test = await self.lab_tests_repo.get_lab_test_by_id(
            lab_test_id, branchId=branchId
        )
        if lab_test is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LabTest not found",
            )
        return lab_test

    async def update_lab_test_by_id(
        self, lab_test_id: str, body: UpdateLabTest
    ) -> LabTestInDb:
        updated_lab_test = await self.lab_tests_repo.update_lab_test_by_id(
            lab_test_id, body
        )
        if updated_lab_test is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LabTest not found",
            )
        return updated_lab_test

    async def delete_lab_test_by_id(self, lab_test_id: str) -> LabTestInDb:
        deleted_lab_test = await self.lab_tests_repo.delete_lab_test_by_id(lab_test_id)
        if deleted_lab_test is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LabTest not found",
            )
        return deleted_lab_test


lab_tests_controller = LabTestsController(
    lab_tests_repo=LabTestsRepository.get_instance(),
)
