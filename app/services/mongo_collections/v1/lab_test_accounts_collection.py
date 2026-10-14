from typing import Any

from pymongo import IndexModel, ReturnDocument
from services import BaseMongoCollection


from tools.time_tools import TimeTools


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

    async def fetch_by_id(
        self, account_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one(
            {"id": account_id, "isDeleted": False},
            session=session,
        )

    async def fetch_all(
        self,
        branchId: str | None = None,
        labTestId: str | None = None,
        session: Any = None,
    ) -> list[dict[str, Any]]:
        collection = self._collection
        query: dict[str, Any] = {"isDeleted": False}
        if branchId:
            query["branchId"] = branchId
        if labTestId:
            query["labTestId"] = labTestId
        cursor = collection.find(query, session=session)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def fetch_by_branch_and_test(
        self, branchId: str, labTestId: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one(
            {
                "branchId": branchId,
                "labTestId": labTestId,
                "isDeleted": False,
            },
            session=session,
        )

    async def fetch_by_branch(
        self, branchId: str, session: Any = None
    ) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find(
            {"branchId": branchId, "isDeleted": False}, session=session
        )
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def fetch_by_test_id(
        self, labTestId: str, session: Any = None
    ) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find(
            {"labTestId": labTestId, "isDeleted": False}, session=session
        )
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def update_commercial(
        self, account_id: str, commercial: dict[str, Any], session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        update_doc: dict[str, Any] = {
            "updatedAt": TimeTools.get_now_in_milliseconds()
        }
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
        branchId: str,
        labTestId: str,
        commercial: dict[str, Any],
        session: Any = None,
    ) -> dict[str, Any] | None:
        collection = self._collection
        update_doc: dict[str, Any] = {
            "updatedAt": TimeTools.get_now_in_milliseconds()
        }
        for key, val in commercial.items():
            update_doc[f"commercial.{key}"] = val

        result = await collection.find_one_and_update(
            {
                "branchId": branchId,
                "labTestId": labTestId,
                "isDeleted": False,
            },
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        return result

    async def delete_by_test_id(
        self, labTestId: str, session: Any = None
    ) -> None:
        collection = self._collection
        await collection.update_many(
            {"labTestId": labTestId},
            {"$set": {"isDeleted": True, "updatedAt": TimeTools.get_now_in_milliseconds()}},
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
