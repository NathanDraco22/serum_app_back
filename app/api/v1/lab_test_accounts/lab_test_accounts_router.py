from fastapi import APIRouter, Depends
from serum.repos.v1.common.filter_params import LabTestAccountFilterParams
from serum.repos.v1.lab_test_accounts import (
    LabTestAccountInDb,
    UpdateLabTestAccountCommercial,
)
from responses.v1 import ListResponse

from .lab_test_accounts_controller import lab_test_accounts_controller

lab_test_accounts_router = APIRouter(tags=["lab_test_accountsV1"])


@lab_test_accounts_router.get("")
async def get_all_accounts(
    query_params: LabTestAccountFilterParams = Depends(),
) -> ListResponse[LabTestAccountInDb]:
    return await lab_test_accounts_controller.get_all_accounts(
        branchId=query_params.branchId,
        labTestId=query_params.labTestId,
    )


@lab_test_accounts_router.get("/branch/{branchId}")
async def get_accounts_by_branch(
    branchId: str,
) -> ListResponse[LabTestAccountInDb]:
    return await lab_test_accounts_controller.get_accounts_by_branch(branchId)


@lab_test_accounts_router.get("/test/{labTestId}")
async def get_accounts_by_test(
    labTestId: str,
) -> ListResponse[LabTestAccountInDb]:
    return await lab_test_accounts_controller.get_accounts_by_test(labTestId)


@lab_test_accounts_router.get("/branch/{branchId}/test/{labTestId}")
async def get_by_branch_and_test(
    branchId: str, labTestId: str
) -> LabTestAccountInDb:
    return await lab_test_accounts_controller.get_by_branch_and_test(
        branchId, labTestId
    )


@lab_test_accounts_router.get("/{account_id}")
async def get_account_by_id(account_id: str) -> LabTestAccountInDb:
    return await lab_test_accounts_controller.get_account_by_id(account_id)


@lab_test_accounts_router.patch("/{account_id}/commercial")
async def update_commercial(
    account_id: str, body: UpdateLabTestAccountCommercial
) -> LabTestAccountInDb:
    return await lab_test_accounts_controller.update_commercial(account_id, body)


@lab_test_accounts_router.patch("/branch/{branchId}/test/{labTestId}/commercial")
async def update_commercial_by_branch_and_test(
    branchId: str, labTestId: str, body: UpdateLabTestAccountCommercial
) -> LabTestAccountInDb:
    return await lab_test_accounts_controller.update_commercial_by_branch_and_test(
        branchId, labTestId, body
    )
