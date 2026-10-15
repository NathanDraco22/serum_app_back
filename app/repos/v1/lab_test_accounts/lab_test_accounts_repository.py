from typing import Any

from tools.time_tools import TimeTools
from tools.uuid_tool import UuidTool

from .data.lab_test_accounts_datasource import LabTestAccountsDataSource
from .models.lab_test_account_model import (
    CreateLabTestAccount,
    LabTestAccountInDb,
    UpdateLabTestAccountCommercial,
)


class LabTestAccountsRepository:
    _instance: "LabTestAccountsRepository|None" = None

    def __init__(self, ds: LabTestAccountsDataSource):
        self.ds = ds

    @classmethod
    def get_instance(cls) -> "LabTestAccountsRepository":
        if cls._instance is None:
            cls._instance = cls(LabTestAccountsDataSource())
        return cls._instance

    async def create_account(
        self, create_model: CreateLabTestAccount, session: Any = None
    ) -> LabTestAccountInDb:
        account_in_db = LabTestAccountInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_model.model_dump(),
        )
        result = await self.ds.create_account(
            account_in_db.model_dump(), session=session
        )
        return LabTestAccountInDb.model_validate(result)

    async def create_accounts_batch(
        self, create_models: list[CreateLabTestAccount], session: Any = None
    ) -> list[LabTestAccountInDb]:
        now = TimeTools.get_now_in_milliseconds()
        accounts_in_db = [
            LabTestAccountInDb(
                id=UuidTool.generate_uuid(),
                createdAt=now,
                **m.model_dump(),
            )
            for m in create_models
        ]
        docs = [acc.model_dump() for acc in accounts_in_db]
        await self.ds.create_accounts_batch(docs, session=session)
        return accounts_in_db

    async def get_by_id(
        self, account_id: str, session: Any = None
    ) -> LabTestAccountInDb | None:
        result = await self.ds.get_by_id(account_id, session=session)
        if result is None:
            return None
        return LabTestAccountInDb.model_validate(result)

    async def get_all(
        self,
        branchId: str | None = None,
        labTestId: str | None = None,
        session: Any = None,
    ) -> list[LabTestAccountInDb]:
        results = await self.ds.get_all(
            branchId=branchId, labTestId=labTestId, session=session
        )
        return [LabTestAccountInDb.model_validate(r) for r in results]

    async def get_by_branch_and_test(
        self, branchId: str, labTestId: str, session: Any = None
    ) -> LabTestAccountInDb | None:
        result = await self.ds.get_by_branch_and_test(
            branchId, labTestId, session=session
        )
        if result is None:
            return None
        return LabTestAccountInDb.model_validate(result)

    async def get_by_branch(
        self, branchId: str, session: Any = None
    ) -> list[LabTestAccountInDb]:
        results = await self.ds.get_by_branch(branchId, session=session)
        return [LabTestAccountInDb.model_validate(r) for r in results]

    async def get_by_test_id(
        self, labTestId: str, session: Any = None
    ) -> list[LabTestAccountInDb]:
        results = await self.ds.get_by_test_id(labTestId, session=session)
        return [LabTestAccountInDb.model_validate(r) for r in results]

    async def update_commercial(
        self,
        account_id: str,
        update_model: UpdateLabTestAccountCommercial,
        session: Any = None,
    ) -> LabTestAccountInDb | None:
        commercial_data = update_model.model_dump(exclude_none=True)
        result = await self.ds.update_commercial(
            account_id, commercial_data, session=session
        )
        if result is None:
            return None
        return LabTestAccountInDb.model_validate(result)

    async def update_commercial_by_branch_and_test(
        self,
        branchId: str,
        labTestId: str,
        update_model: UpdateLabTestAccountCommercial,
        session: Any = None,
    ) -> LabTestAccountInDb | None:
        commercial_data = update_model.model_dump(exclude_none=True)
        result = await self.ds.update_commercial_by_branch_and_test(
            branchId, labTestId, commercial_data, session=session
        )
        if result is None:
            return None
        return LabTestAccountInDb.model_validate(result)
