from typing import Any
from serum.services.mongo_collections.v1 import CashMovementsCollection


class CashMovementsDataSource:
    async def create_cash_movement(
        self, cash_movement: dict[str, Any], session: Any = None
    ) -> dict[str, Any]:
        collection = CashMovementsCollection.get_instance()
        await collection.create_cash_movement(cash_movement, session=session)
        return cash_movement

    async def get_all_cash_movements(
        self, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        collection = CashMovementsCollection.get_instance()
        return await collection.fetch_all_cash_movements(filters)

    async def get_cash_movement_by_id(
        self, cash_movement_id: str
    ) -> dict[str, Any] | None:
        collection = CashMovementsCollection.get_instance()
        return await collection.fetch_cash_movement_by_id(cash_movement_id)

    async def update_cash_movement_by_id(
        self, cash_movement_id: str, cash_movement: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = CashMovementsCollection.get_instance()
        return await collection.update_cash_movement_by_id(
            cash_movement_id, cash_movement
        )

    async def delete_cash_movement_by_id(
        self, cash_movement_id: str
    ) -> dict[str, Any] | None:
        collection = CashMovementsCollection.get_instance()
        return await collection.delete_cash_movement_by_id(cash_movement_id)
