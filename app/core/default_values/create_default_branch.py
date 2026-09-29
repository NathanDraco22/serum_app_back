from repos.v1.branches.models.branch_model import BranchInDb
from services.mongo_collections.v1.branches_collection import BranchesCollection
from tools.time_tools import TimeTools

ORIGIN_BRANCH_ID = "ORIGIN_BRANCH"
ORIGIN_BRANCH_NAME = "Origen"


async def create_default_branch(branch_name: str | None = None) -> BranchInDb:
    target_branch_name = branch_name if branch_name is not None else ORIGIN_BRANCH_NAME
    new_branch = BranchInDb(
        id=ORIGIN_BRANCH_ID,
        name=target_branch_name,
        address="Sede Principal",
        phone="00000000",
        createdAt=TimeTools.get_now_in_milliseconds(),
    )

    await BranchesCollection.get_instance().create_branch_if_absent(
        ORIGIN_BRANCH_ID, new_branch.model_dump()
    )

    return new_branch
