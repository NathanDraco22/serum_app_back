from typing import Any

from pymongo import ReturnDocument
from services import BaseMongoCollection


class CashRegistersCollection(BaseMongoCollection):
    collection_name = "CashRegisters"

    async def create_cash_register(self, cash_register: dict) -> None:
        collection = self._collection
        await collection.insert_one(cash_register)

    async def fetch_all_cash_registers(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_cash_register_by_id(
        self, cash_register_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": cash_register_id})
        return result

    async def fetch_open_register_by_branch(
        self, branch_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"branchId": branch_id, "isOpen": True})
        return result

    async def update_cash_register_by_id(
        self,
        cash_register_id: str,
        cash_register: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": cash_register_id},
            {"$set": cash_register},
            return_document=ReturnDocument.AFTER,
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
