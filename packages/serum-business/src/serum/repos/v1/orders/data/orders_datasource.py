from typing import Any

from serum.services.mongo_collections.v1 import OrdersCollection


class OrdersDataSource:
    async def create_order(self, order: dict[str, Any]) -> dict[str, Any]:
        collection = OrdersCollection.get_instance()
        await collection.create_order(order)
        return order

    async def get_all_orders(
        self, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        collection = OrdersCollection.get_instance()
        return await collection.fetch_all_orders(filters)

    async def get_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        collection = OrdersCollection.get_instance()
        return await collection.fetch_order_by_id(order_id)

    async def update_order_by_id(
        self, order_id: str, order: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = OrdersCollection.get_instance()
        return await collection.update_order_by_id(order_id, order)

    async def delete_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        collection = OrdersCollection.get_instance()
        return await collection.delete_order_by_id(order_id)
