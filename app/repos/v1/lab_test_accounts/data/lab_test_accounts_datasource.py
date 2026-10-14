from typing import Any

from services.mongo_collections.v1 import LabTestAccountsCollection


class LabTestAccountsDataSource:
    async def create_account(
        self, account: dict[str, Any], session: Any = None
    ) -> dict[str, Any]:
        col = LabTestAccountsCollection.get_instance()
        await col.create_account(account, session=session)
        return account

    async def create_accounts_batch(
        self, accounts: list[dict[str, Any]], session: Any = None
    ) -> list[dict[str, Any]]:
        col = LabTestAccountsCollection.get_instance()
        await col.create_accounts_batch(accounts, session=session)
        return accounts

    async def get_by_id(
        self, account_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        col = LabTestAccountsCollection.get_instance()
        return await col.fetch_by_id(account_id, session=session)

    async def get_all(
        self,
        branchId: str | None = None,
        labTestId: str | None = None,
        session: Any = None,
    ) -> list[dict[str, Any]]:
        col = LabTestAccountsCollection.get_instance()
        return await col.fetch_all(
            branchId=branchId, labTestId=labTestId, session=session
        )

    async def get_by_branch_and_test(
        self, branchId: str, labTestId: str, session: Any = None
    ) -> dict[str, Any] | None:
        col = LabTestAccountsCollection.get_instance()
        return await col.fetch_by_branch_and_test(
            branchId, labTestId, session=session
        )

    async def get_by_branch(
        self, branchId: str, session: Any = None
    ) -> list[dict[str, Any]]:
        col = LabTestAccountsCollection.get_instance()
        return await col.fetch_by_branch(branchId, session=session)

    async def get_by_test_id(
        self, labTestId: str, session: Any = None
    ) -> list[dict[str, Any]]:
        col = LabTestAccountsCollection.get_instance()
        return await col.fetch_by_test_id(labTestId, session=session)

    async def update_commercial(
        self, account_id: str, commercial: dict[str, Any], session: Any = None
    ) -> dict[str, Any] | None:
        col = LabTestAccountsCollection.get_instance()
        return await col.update_commercial(account_id, commercial, session=session)

    async def update_commercial_by_branch_and_test(
        self,
        branchId: str,
        labTestId: str,
        commercial: dict[str, Any],
        session: Any = None,
    ) -> dict[str, Any] | None:
        col = LabTestAccountsCollection.get_instance()
        return await col.update_commercial_by_branch_and_test(
            branchId, labTestId, commercial, session=session
        )
