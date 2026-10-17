from fastapi import APIRouter, Query

from serum.repos.v1.lab_tests import CreateLabTest, LabTestInDb, UpdateLabTest
from responses.v1 import ListResponse

from .lab_tests_controller import lab_tests_controller

lab_tests_router = APIRouter(tags=["lab_testsV1"])


@lab_tests_router.post("")
async def create_lab_test(body: CreateLabTest) -> LabTestInDb:
    return await lab_tests_controller.create_lab_test(body)


@lab_tests_router.get("")
async def get_all_lab_tests(
    branchId: str | None = Query(None),
    branch_id: str | None = Query(None),
) -> ListResponse[LabTestInDb]:
    effective_branch = branchId or branch_id
    return await lab_tests_controller.get_all_lab_tests(branchId=effective_branch)


@lab_tests_router.get("/search/{text_query}")
async def search_lab_test_by_text(
    text_query: str,
    branchId: str | None = Query(None),
    branch_id: str | None = Query(None),
) -> ListResponse[LabTestInDb]:
    effective_branch = branchId or branch_id
    return await lab_tests_controller.search_lab_test_by_text(
        text_query, branchId=effective_branch
    )


@lab_tests_router.get("/{lab_test_id}")
async def get_lab_test_by_id(
    lab_test_id: str,
    branchId: str | None = Query(None),
    branch_id: str | None = Query(None),
) -> LabTestInDb:
    effective_branch = branchId or branch_id
    return await lab_tests_controller.get_lab_test_by_id(
        lab_test_id, branchId=effective_branch
    )


@lab_tests_router.patch("/{lab_test_id}")
async def update_lab_test_by_id(lab_test_id: str, body: UpdateLabTest) -> LabTestInDb:
    return await lab_tests_controller.update_lab_test_by_id(lab_test_id, body)


@lab_tests_router.delete("/{lab_test_id}")
async def delete_lab_test_by_id(lab_test_id: str) -> LabTestInDb:
    return await lab_tests_controller.delete_lab_test_by_id(lab_test_id)
