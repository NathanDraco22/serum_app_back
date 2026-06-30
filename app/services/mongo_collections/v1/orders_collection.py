from typing import Any

from pymongo import ReturnDocument
from services import BaseMongoCollection


class OrdersCollection(BaseMongoCollection):
    collection_name = "Orders"

    async def create_order(self, order: dict) -> None:
        collection = self._collection
        await collection.insert_one(order)

    async def fetch_all_orders(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": order_id})
        return result

    async def update_order_by_id(
        self,
        order_id: str,
        order: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": order_id},
            {"$set": order},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": order_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
