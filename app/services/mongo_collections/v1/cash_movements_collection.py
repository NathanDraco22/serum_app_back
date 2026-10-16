from typing import Any

from pymongo import ReturnDocument
from services import BaseMongoCollection


class CashMovementsCollection(BaseMongoCollection):
    collection_name = "CashMovements"

    async def create_cash_movement(
        self, cash_movement: dict, session: Any = None
    ) -> None:
        collection = self._collection
        await collection.insert_one(cash_movement, session=session)

    async def fetch_all_cash_movements(
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

    async def fetch_cash_movement_by_id(
        self, cash_movement_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"id": cash_movement_id, "isDeleted": {"$ne": True}},
            session=session,
        )
        return result

    async def update_cash_movement_by_id(
        self,
        cash_movement_id: str,
        cash_movement: dict,
        session: Any = None,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": cash_movement_id, "isDeleted": {"$ne": True}},
            {"$set": cash_movement},
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_cash_movement_by_id(
        self, cash_movement_id: str, session: Any = None, now: int | None = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        set_dict: dict[str, Any] = {"isDeleted": True}
        if now is not None:
            set_dict["updatedAt"] = now

        result = await collection.find_one_and_update(
            {"id": cash_movement_id, "isDeleted": {"$ne": True}},
            {"$set": set_dict},
            session=session,
            return_document=ReturnDocument.AFTER,
        )
        return result
