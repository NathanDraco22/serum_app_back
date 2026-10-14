from tools.time_tools import TimeTools
from tools.uuid_tool import UuidTool

from .data.branches_datasource import BranchesDataSource
from .models.branch_model import BranchInDb, CreateBranch, UpdateBranch


class BranchesRepository:
    _instance: "BranchesRepository|None" = None

    def __init__(self, branches_ds: BranchesDataSource):
        self.branches_ds = branches_ds

    @classmethod
    def get_instance(cls) -> "BranchesRepository":
        if cls._instance is None:
            cls._instance = cls(BranchesDataSource())
        return cls._instance

    async def create_branch(self, create_branch: CreateBranch) -> BranchInDb:
        new_branch = BranchInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            **create_branch.model_dump(),
        )
        result = await self.branches_ds.create_branch(new_branch.model_dump())

        # Auto-provisionar cuentas de pruebas de laboratorio para esta nueva sede
        try:
            from services.mongo_collections.v1 import (
                LabTestAccountsCollection,
                LabTestsCollection,
            )

            lab_tests = await LabTestsCollection.get_instance().fetch_all_lab_tests()
            if lab_tests:
                accounts_col = LabTestAccountsCollection.get_instance()
                new_accounts = [
                    {
                        "id": UuidTool.generate_uuid(),
                        "branchId": new_branch.id,
                        "labTestId": t["id"],
                        "commercial": {
                            "salePrice": 0,
                            "salePrice2": 0,
                            "costPrice": 0,
                            "currency": t.get("currency", "USD"),
                        },
                        "createdAt": new_branch.createdAt,
                        "updatedAt": None,
                        "isDeleted": False,
                    }
                    for t in lab_tests
                ]
                await accounts_col.create_accounts_batch(new_accounts)
        except Exception:
            pass

        return BranchInDb.model_validate(result)

    async def get_all_branches(self) -> list[BranchInDb]:
        results = await self.branches_ds.get_all_branches()
        return [BranchInDb.model_validate(r) for r in results]

    async def get_branch_by_id(self, branch_id: str) -> BranchInDb | None:
        result = await self.branches_ds.get_branch_by_id(branch_id)
        if result is None:
            return None
        return BranchInDb.model_validate(result)

    async def update_branch_by_id(
        self, branch_id: str, branch: UpdateBranch
    ) -> BranchInDb | None:
        updated_data = branch.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.branches_ds.update_branch_by_id(branch_id, updated_data)
        if result is None:
            return None
        return BranchInDb.model_validate(result)

    async def delete_branch_by_id(self, branch_id: str) -> BranchInDb | None:
        result = await self.branches_ds.delete_branch_by_id(branch_id)
        if result is None:
            return None
        return BranchInDb.model_validate(result)
