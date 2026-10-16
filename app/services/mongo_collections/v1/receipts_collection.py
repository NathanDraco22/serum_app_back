from typing import Any
from pymongo import ReturnDocument
from services import BaseMongoCollection


class ReceiptsCollection(BaseMongoCollection):
    collection_name = "Receipts"

    async def create_receipt(
        self, receipt: dict, session: Any = None
    ) -> None:
        collection = self._collection
        await collection.insert_one(receipt, session=session)

    async def fetch_all_receipts(
        self, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        collection = self._collection
        query: dict[str, Any] = {"isDeleted": {"$ne": True}}

        offset = 0
        limit = 0

        if filters:
            query_filters = filters.copy()
            offset = query_filters.pop("offset", 0)
            limit = query_filters.pop("limit", 0)

            start_date = query_filters.pop("startDate", None)
            end_date = query_filters.pop("endDate", None)

            if start_date is not None or end_date is not None:
                query["createdAt"] = {}
                if start_date is not None:
                    query["createdAt"]["$gte"] = start_date
                if end_date is not None:
                    query["createdAt"]["$lte"] = end_date

            for key, value in query_filters.items():
                if value is not None:
                    query[key] = value

        cursor = collection.find(query).sort("createdAt", -1)

        if offset > 0:
            cursor = cursor.skip(offset)
        if limit > 0:
            cursor = cursor.limit(limit)

        result = await cursor.to_list(length=limit if limit > 0 else None)
        await cursor.close()

        return result

    async def fetch_receipt_by_id(self, receipt_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"id": receipt_id, "isDeleted": {"$ne": True}}
        )
        return result

    async def update_receipt_by_id(
        self,
        receipt_id: str,
        receipt: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": receipt_id, "isDeleted": {"$ne": True}},
            {"$set": receipt},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_receipt_by_id(self, receipt_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": receipt_id, "isDeleted": {"$ne": True}},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
