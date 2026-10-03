from typing import Any
from services.mongo_collections.v1 import CashShiftsCollection


class CashShiftsDataSource:
    async def create_cash_shift(
        self, cash_shift: dict[str, Any]
    ) -> dict[str, Any]:
        collection = CashShiftsCollection.get_instance()
        await collection.create_cash_shift(cash_shift)
        return cash_shift

    async def get_all_cash_shifts(
        self, filter_dict: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        collection = CashShiftsCollection.get_instance()
        return await collection.fetch_all_cash_shifts(filter_dict)

    async def get_cash_shift_by_id(
        self, cash_shift_id: str
    ) -> dict[str, Any] | None:
        collection = CashShiftsCollection.get_instance()
        return await collection.fetch_cash_shift_by_id(cash_shift_id)

    async def get_active_shift_by_user(
        self, user_id: str
    ) -> dict[str, Any] | None:
        collection = CashShiftsCollection.get_instance()
        return await collection.fetch_active_shift_by_user(user_id)

    async def update_cash_shift_by_id(
        self, cash_shift_id: str, cash_shift: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = CashShiftsCollection.get_instance()
        return await collection.update_cash_shift_by_id(cash_shift_id, cash_shift)

    async def delete_cash_shift_by_id(
        self, cash_shift_id: str
    ) -> dict[str, Any] | None:
        collection = CashShiftsCollection.get_instance()
        return await collection.delete_cash_shift_by_id(cash_shift_id)

    async def add_to_balance(
        self, shift_id: str, payment_method: str, amount: int
    ) -> dict[str, Any] | None:
        collection = CashShiftsCollection.get_instance()
        return await collection.add_to_balance(shift_id, payment_method, amount)
