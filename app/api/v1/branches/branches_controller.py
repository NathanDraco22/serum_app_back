from fastapi import HTTPException, status

from repos.v1.branches import (
    BranchesRepository,
    BranchInDb,
    CreateBranch,
    UpdateBranch,
)
from responses.v1 import ListResponse


class BranchesController:
    def __init__(self, branches_repo: BranchesRepository) -> None:
        self.branches_repo = branches_repo

    async def create_branch(self, body: CreateBranch) -> BranchInDb:
        return await self.branches_repo.create_branch(body)

    async def get_all_branches(self) -> ListResponse[BranchInDb]:
        branches = await self.branches_repo.get_all_branches()
        return ListResponse(count=len(branches), data=branches)

    async def get_branch_by_id(self, branch_id: str) -> BranchInDb:
        branch = await self.branches_repo.get_branch_by_id(branch_id)
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found",
            )
        return branch

    async def update_branch_by_id(
        self, branch_id: str, body: UpdateBranch
    ) -> BranchInDb:
        updated_branch = await self.branches_repo.update_branch_by_id(branch_id, body)
        if updated_branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found",
            )
        return updated_branch

    async def delete_branch_by_id(self, branch_id: str) -> BranchInDb:
        deleted_branch = await self.branches_repo.delete_branch_by_id(branch_id)
        if deleted_branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found",
            )
        return deleted_branch


branches_controller = BranchesController(
    branches_repo=BranchesRepository.get_instance(),
)
