from fastapi import APIRouter

from repos.v1.lab_tests import CreateLabTest, UpdateLabTest, LabTestInDb
from responses.v1 import ListResponse

from .lab_tests_controller import lab_tests_controller


lab_tests_router = APIRouter(tags=["lab_testsV1"])


@lab_tests_router.post("")
async def create_lab_test(body: CreateLabTest) -> LabTestInDb:
    return await lab_tests_controller.create_lab_test(body)


@lab_tests_router.get("")
async def get_all_lab_tests() -> ListResponse[LabTestInDb]:
    return await lab_tests_controller.get_all_lab_tests()


@lab_tests_router.get("/{lab_test_id}")
async def get_lab_test_by_id(lab_test_id: str) -> LabTestInDb:
    return await lab_tests_controller.get_lab_test_by_id(lab_test_id)


@lab_tests_router.patch("/{lab_test_id}")
async def update_lab_test_by_id(lab_test_id: str, body: UpdateLabTest) -> LabTestInDb:
    return await lab_tests_controller.update_lab_test_by_id(lab_test_id, body)


@lab_tests_router.delete("/{lab_test_id}")
async def delete_lab_test_by_id(lab_test_id: str) -> LabTestInDb:
    return await lab_tests_controller.delete_lab_test_by_id(lab_test_id)
