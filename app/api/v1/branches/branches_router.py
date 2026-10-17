from fastapi import APIRouter

from serum.repos.v1.branches import BranchInDb, CreateBranch, UpdateBranch
from responses.v1 import ListResponse

from .branches_controller import branches_controller

branches_router = APIRouter(tags=["branchesV1"])


@branches_router.post("")
async def create_branch(body: CreateBranch) -> BranchInDb:
    return await branches_controller.create_branch(body)


@branches_router.get("")
async def get_all_branches() -> ListResponse[BranchInDb]:
    return await branches_controller.get_all_branches()


@branches_router.get("/{branch_id}")
async def get_branch_by_id(branch_id: str) -> BranchInDb:
    return await branches_controller.get_branch_by_id(branch_id)


@branches_router.patch("/{branch_id}")
async def update_branch_by_id(branch_id: str, body: UpdateBranch) -> BranchInDb:
    return await branches_controller.update_branch_by_id(branch_id, body)


@branches_router.delete("/{branch_id}")
async def delete_branch_by_id(branch_id: str) -> BranchInDb:
    return await branches_controller.delete_branch_by_id(branch_id)
