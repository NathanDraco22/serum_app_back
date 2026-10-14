from typing import Any

from pymongo import IndexModel, ReturnDocument
from services import BaseMongoCollection


class LabTestAccountsCollection(BaseMongoCollection):
    collection_name = "LabTestAccounts"

    async def create_account(
        self, account: dict[str, Any], session: Any = None
    ) -> None:
        collection = self._collection
        await collection.insert_one(account, session=session)

    async def create_accounts_batch(
        self, accounts: list[dict[str, Any]], session: Any = None
    ) -> None:
        if not accounts:
            return
        collection = self._collection
        await collection.insert_many(accounts, session=session)

    async def fetch_by_branch_and_test(
        self, branch_id: str, lab_test_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one(
            {
                "branchId": branch_id,
                "labTestId": lab_test_id,
                "isDeleted": False,
            },
            session=session,
        )

    async def fetch_by_branch(
        self, branch_id: str, session: Any = None
    ) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find(
            {"branchId": branch_id, "isDeleted": False}, session=session
        )
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def fetch_by_test_id(
        self, lab_test_id: str, session: Any = None
    ) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find(
            {"labTestId": lab_test_id, "isDeleted": False}, session=session
        )
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def update_commercial(
        self, account_id: str, commercial: dict[str, Any], session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        update_doc: dict[str, Any] = {}
        for key, val in commercial.items():
            update_doc[f"commercial.{key}"] = val

        result = await collection.find_one_and_update(
            {"id": account_id, "isDeleted": False},
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        return result

    async def update_commercial_by_branch_and_test(
        self,
        branch_id: str,
        lab_test_id: str,
        commercial: dict[str, Any],
        session: Any = None,
    ) -> dict[str, Any] | None:
        collection = self._collection
        update_doc: dict[str, Any] = {}
        for key, val in commercial.items():
            update_doc[f"commercial.{key}"] = val

        result = await collection.find_one_and_update(
            {
                "branchId": branch_id,
                "labTestId": lab_test_id,
                "isDeleted": False,
            },
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        return result

    async def delete_by_test_id(
        self, lab_test_id: str, session: Any = None
    ) -> None:
        collection = self._collection
        await collection.update_many(
            {"labTestId": lab_test_id},
            {"$set": {"isDeleted": True}},
            session=session,
        )

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel(
                    [
                        ("id", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("branchId", 1),
                        ("labTestId", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("labTestId", 1),
                    ],
                ),
            ]
        )
