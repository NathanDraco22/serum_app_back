from typing import Any

from serum.services.mongo_collections.v1 import CashRegistersCollection


class CashRegistersDataSource:
    async def create_cash_register(
        self, cash_register: dict[str, Any]
    ) -> dict[str, Any]:
        collection = CashRegistersCollection.get_instance()
        await collection.create_cash_register(cash_register)
        return cash_register

    async def get_all_cash_registers(self) -> list[dict[str, Any]]:
        collection = CashRegistersCollection.get_instance()
        return await collection.fetch_all_cash_registers()

    async def get_cash_register_by_id(
        self, cash_register_id: str
    ) -> dict[str, Any] | None:
        collection = CashRegistersCollection.get_instance()
        return await collection.fetch_cash_register_by_id(cash_register_id)

    async def get_open_register_by_branch(
        self, branch_id: str
    ) -> dict[str, Any] | None:
        collection = CashRegistersCollection.get_instance()
        return await collection.fetch_open_register_by_branch(branch_id)

    async def update_cash_register_by_id(
        self, cash_register_id: str, cash_register: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = CashRegistersCollection.get_instance()
        return await collection.update_cash_register_by_id(
            cash_register_id, cash_register
        )

    async def delete_cash_register_by_id(
        self, cash_register_id: str
    ) -> dict[str, Any] | None:
        collection = CashRegistersCollection.get_instance()
        return await collection.delete_cash_register_by_id(cash_register_id)
