from typing import Any

from pymongo import ReturnDocument
from serum.services import BaseMongoCollection


class CashRegistersCollection(BaseMongoCollection):
    collection_name = "CashRegisters"

    async def create_cash_register(self, cash_register: dict) -> None:
        collection = self._collection
        await collection.insert_one(cash_register)

    async def create_cash_register_if_absent(
        self, cash_register_id: str, cash_register: dict
    ) -> None:
        collection = self._collection
        await collection.update_one(
            {"id": cash_register_id},
            {"$setOnInsert": cash_register},
            upsert=True,
        )

    async def fetch_all_cash_registers(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({"isDeleted": {"$ne": True}})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_cash_register_by_id(
        self, cash_register_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"id": cash_register_id, "isDeleted": {"$ne": True}}, session=session
        )
        return result

    async def fetch_open_register_by_branch(
        self, branch_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"branchId": branch_id, "isOpen": True, "isDeleted": {"$ne": True}})
        return result

    async def update_cash_register_by_id(
        self,
        cash_register_id: str,
        cash_register: dict,
        session: Any = None,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": cash_register_id},
            {"$set": cash_register},
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def delete_cash_register_by_id(
        self, cash_register_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": cash_register_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def add_to_balance(
        self,
        register_id: str,
        payment_method: str,
        amount: int,
        session: Any = None,
    ) -> dict[str, Any] | None:
        balance_field = f"{payment_method}Balance"
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": register_id},
            {"$inc": {balance_field: amount, "totalBalance": amount}},
            session=session,
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def subtract_from_balance(
        self,
        register_id: str,
        payment_method: str,
        amount: int,
        session: Any = None,
    ) -> dict[str, Any] | None:
        balance_field = f"{payment_method}Balance"
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": register_id},
            {"$inc": {balance_field: -amount, "totalBalance": -amount}},
            session=session,
            return_document=ReturnDocument.AFTER,
        )
        return result
