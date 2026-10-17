from typing import Any

from pymongo import ReturnDocument
from serum.services import BaseMongoCollection


class CashShiftsCollection(BaseMongoCollection):
    collection_name = "CashShifts"

    async def create_cash_shift(self, cash_shift: dict) -> None:
        collection = self._collection
        await collection.insert_one(cash_shift)

    async def fetch_all_cash_shifts(
        self, filter_dict: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        collection = self._collection
        query: dict[str, Any] = {"isDeleted": {"$ne": True}}
        if filter_dict:
            query.update(filter_dict)

        cursor = collection.find(query).sort("openedAt", -1)
        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_cash_shift_by_id(
        self, cash_shift_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"id": cash_shift_id, "isDeleted": {"$ne": True}},
            session=session,
        )
        return result

    async def fetch_active_shift_by_user(
        self, user_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"userId": user_id, "status": "OPEN", "isDeleted": {"$ne": True}},
            session=session,
        )
        return result

    async def update_cash_shift_by_id(
        self,
        cash_shift_id: str,
        cash_shift: dict[str, Any],
        session: Any = None,
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": cash_shift_id},
            {"$set": cash_shift},
            session=session,
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def delete_cash_shift_by_id(
        self, cash_shift_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": cash_shift_id},
            {"$set": {"isDeleted": True}},
            session=session,
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def add_to_balance(
        self,
        shift_id: str,
        payment_method: str,
        amount: int,
        session: Any = None,
    ) -> dict[str, Any] | None:
        balance_field = f"{payment_method}Balance"
        collection = self._collection
        query: dict[str, Any] = {
            "id": shift_id,
            "status": "OPEN",
            "isDeleted": {"$ne": True},
        }

        if amount < 0:
            required = abs(amount)
            if payment_method == "cash":
                query["$expr"] = {
                    "$gte": [
                        {"$add": ["$initialBalance", "$cashBalance"]},
                        required,
                    ]
                }
            else:
                query[balance_field] = {"$gte": required}

        result = await collection.find_one_and_update(
            query,
            {"$inc": {balance_field: amount, "totalBalance": amount}},
            session=session,
            return_document=ReturnDocument.AFTER,
        )
        return result
