from typing import Any

from pymongo import ReturnDocument
from services import BaseMongoCollection


class QuotationsCollection(BaseMongoCollection):
    collection_name = "Quotations"

    async def create_quotation(self, quotation: dict) -> None:
        collection = self._collection
        await collection.insert_one(quotation)

    async def fetch_all_quotations(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_quotation_by_id(self, quotation_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": quotation_id})
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
