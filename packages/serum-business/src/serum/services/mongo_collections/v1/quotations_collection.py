from typing import Any

from pymongo import ReturnDocument

from serum.services import BaseMongoCollection


from serum.tools.time_tools import TimeTools


class QuotationsCollection(BaseMongoCollection):
    collection_name = "Quotations"

    async def create_quotation(self, quotation: dict) -> None:
        collection = self._collection
        await collection.insert_one(quotation)

    async def fetch_all_quotations(
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

            # Filtro fijo de 30 días si no se especifica startDate
            if start_date is None:
                now_ms = TimeTools.get_now_in_milliseconds()
                start_date = now_ms - (30 * 24 * 60 * 60 * 1000)

            query["createdAt"] = {"$gte": start_date}
            if end_date is not None:
                query["createdAt"]["$lte"] = end_date

            for key, value in query_filters.items():
                if value is not None:
                    query[key] = value
        else:
            # Si no se pasan filtros, aplica el filtro fijo de 30 días por defecto
            now_ms = TimeTools.get_now_in_milliseconds()
            start_date = now_ms - (30 * 24 * 60 * 60 * 1000)
            query["createdAt"] = {"$gte": start_date}

        cursor = collection.find(query).sort("createdAt", -1)

        if offset > 0:
            cursor = cursor.skip(offset)
        if limit > 0:
            cursor = cursor.limit(limit)

        result = await cursor.to_list(length=limit if limit > 0 else None)
        await cursor.close()

        return result

    async def fetch_quotation_by_id(self, quotation_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": quotation_id, "isDeleted": {"$ne": True}})
        return result

    async def update_quotation_by_id(
        self,
        quotation_id: str,
        quotation: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": quotation_id},
            {"$set": quotation},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_quotation_by_id(self, quotation_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": quotation_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result
