from fastapi import APIRouter
from repos.v1.lab_test_accounts import (
    LabTestAccountInDb,
    UpdateLabTestAccountCommercial,
)
from responses.v1 import ListResponse

from .lab_test_accounts_controller import lab_test_accounts_controller

lab_test_accounts_router = APIRouter(tags=["lab_test_accountsV1"])


@lab_test_accounts_router.get("/branch/{branch_id}")
async def get_accounts_by_branch(
    branch_id: str,
) -> ListResponse[LabTestAccountInDb]:
    return await lab_test_accounts_controller.get_accounts_by_branch(branch_id)


@lab_test_accounts_router.get("/test/{lab_test_id}")
async def get_accounts_by_test(
    lab_test_id: str,
) -> ListResponse[LabTestAccountInDb]:
    return await lab_test_accounts_controller.get_accounts_by_test(lab_test_id)


@lab_test_accounts_router.get("/branch/{branch_id}/test/{lab_test_id}")
async def get_by_branch_and_test(
    branch_id: str, lab_test_id: str
) -> LabTestAccountInDb:
    return await lab_test_accounts_controller.get_by_branch_and_test(
        branch_id, lab_test_id
    )


@lab_test_accounts_router.patch("/{account_id}/commercial")
async def update_commercial(
    account_id: str, body: UpdateLabTestAccountCommercial
) -> LabTestAccountInDb:
    return await lab_test_accounts_controller.update_commercial(account_id, body)


@lab_test_accounts_router.patch("/branch/{branch_id}/test/{lab_test_id}/commercial")
async def update_commercial_by_branch_and_test(
    branch_id: str, lab_test_id: str, body: UpdateLabTestAccountCommercial
) -> LabTestAccountInDb:
    return await lab_test_accounts_controller.update_commercial_by_branch_and_test(
        branch_id, lab_test_id, body
    )
