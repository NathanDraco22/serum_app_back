from fastapi import HTTPException, status
from serum.repos.v1.lab_test_accounts import (
    LabTestAccountInDb,
    LabTestAccountsRepository,
    UpdateLabTestAccountCommercial,
)
from responses.v1 import ListResponse


class LabTestAccountsController:
    def __init__(self, repo: LabTestAccountsRepository) -> None:
        self.repo = repo

    async def get_all_accounts(
        self,
        branchId: str | None = None,
        labTestId: str | None = None,
    ) -> ListResponse[LabTestAccountInDb]:
        accounts = await self.repo.get_all(branchId=branchId, labTestId=labTestId)
        return ListResponse(count=len(accounts), data=accounts)

    async def get_account_by_id(self, account_id: str) -> LabTestAccountInDb:
        account = await self.repo.get_by_id(account_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LabTestAccount not found",
            )
        return account

    async def get_accounts_by_branch(
        self, branchId: str
    ) -> ListResponse[LabTestAccountInDb]:
        accounts = await self.repo.get_by_branch(branchId)
        return ListResponse(count=len(accounts), data=accounts)

    async def get_accounts_by_test(
        self, labTestId: str
    ) -> ListResponse[LabTestAccountInDb]:
        accounts = await self.repo.get_by_test_id(labTestId)
        return ListResponse(count=len(accounts), data=accounts)

    async def get_by_branch_and_test(
        self, branchId: str, labTestId: str
    ) -> LabTestAccountInDb:
        account = await self.repo.get_by_branch_and_test(branchId, labTestId)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LabTestAccount not found",
            )
        return account

    async def update_commercial(
        self, account_id: str, body: UpdateLabTestAccountCommercial
    ) -> LabTestAccountInDb:
        account = await self.repo.update_commercial(account_id, body)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LabTestAccount not found",
            )
        return account

    async def update_commercial_by_branch_and_test(
        self,
        branchId: str,
        labTestId: str,
        body: UpdateLabTestAccountCommercial,
    ) -> LabTestAccountInDb:
        account = await self.repo.update_commercial_by_branch_and_test(
            branchId, labTestId, body
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LabTestAccount not found",
            )
        return account


lab_test_accounts_controller = LabTestAccountsController(
    repo=LabTestAccountsRepository.get_instance()
)
