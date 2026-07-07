from typing import Any

from services.mongo_collections.v1 import CashTransactionsCollection


class CashTransactionsDataSource:
    async def create_cash_transaction(
        self, cash_transaction: dict[str, Any]
    ) -> dict[str, Any]:
        collection = CashTransactionsCollection.get_instance()
        await collection.create_cash_transaction(cash_transaction)
        return cash_transaction

    async def get_all_cash_transactions(
        self, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        collection = CashTransactionsCollection.get_instance()
        return await collection.fetch_all_cash_transactions(filters)

    async def get_cash_transaction_by_id(
        self, cash_transaction_id: str
    ) -> dict[str, Any] | None:
        collection = CashTransactionsCollection.get_instance()
        return await collection.fetch_cash_transaction_by_id(cash_transaction_id)

    async def update_cash_transaction_by_id(
        self, cash_transaction_id: str, cash_transaction: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = CashTransactionsCollection.get_instance()
        return await collection.update_cash_transaction_by_id(
            cash_transaction_id, cash_transaction
        )

    async def delete_cash_transaction_by_id(
        self, cash_transaction_id: str
    ) -> dict[str, Any] | None:
        collection = CashTransactionsCollection.get_instance()
        return await collection.delete_cash_transaction_by_id(cash_transaction_id)
