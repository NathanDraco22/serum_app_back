from fastapi import HTTPException, status

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
        return await self.lab_tests_repo.create_lab_test(body)

    async def get_all_lab_tests(self) -> ListResponse[LabTestInDb]:
        lab_tests = await self.lab_tests_repo.get_all_lab_tests()
        return ListResponse(count=len(lab_tests), data=lab_tests)

    async def get_lab_test_by_id(self, lab_test_id: str) -> LabTestInDb:
        lab_test = await self.lab_tests_repo.get_lab_test_by_id(lab_test_id)
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
