from fastapi import HTTPException, status
from repos.v1.lab_test_accounts import (
    LabTestAccountInDb,
    LabTestAccountsRepository,
    UpdateLabTestAccountCommercial,
)
from responses.v1 import ListResponse


class LabTestAccountsController:
    def __init__(self, repo: LabTestAccountsRepository) -> None:
        self.repo = repo

    async def get_accounts_by_branch(
        self, branch_id: str
    ) -> ListResponse[LabTestAccountInDb]:
        accounts = await self.repo.get_by_branch(branch_id)
        return ListResponse(count=len(accounts), data=accounts)

    async def get_accounts_by_test(
        self, lab_test_id: str
    ) -> ListResponse[LabTestAccountInDb]:
        accounts = await self.repo.get_by_test_id(lab_test_id)
        return ListResponse(count=len(accounts), data=accounts)

    async def get_by_branch_and_test(
        self, branch_id: str, lab_test_id: str
    ) -> LabTestAccountInDb:
        account = await self.repo.get_by_branch_and_test(branch_id, lab_test_id)
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
        branch_id: str,
        lab_test_id: str,
        body: UpdateLabTestAccountCommercial,
    ) -> LabTestAccountInDb:
        account = await self.repo.update_commercial_by_branch_and_test(
            branch_id, lab_test_id, body
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
