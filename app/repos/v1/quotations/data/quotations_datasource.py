from typing import Any

from services.mongo_collections.v1 import QuotationsCollection


class QuotationsDataSource:
    async def create_quotation(self, quotation: dict[str, Any]) -> dict[str, Any]:
        collection = QuotationsCollection.get_instance()
        await collection.create_quotation(quotation)
        return quotation

    async def get_all_quotations(
        self, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        collection = QuotationsCollection.get_instance()
        return await collection.fetch_all_quotations(filters)

    async def get_quotation_by_id(self, quotation_id: str) -> dict[str, Any] | None:
        collection = QuotationsCollection.get_instance()
        return await collection.fetch_quotation_by_id(quotation_id)

    async def update_quotation_by_id(
        self, quotation_id: str, quotation: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = QuotationsCollection.get_instance()
        return await collection.update_quotation_by_id(quotation_id, quotation)

    async def delete_quotation_by_id(self, quotation_id: str) -> dict[str, Any] | None:
        collection = QuotationsCollection.get_instance()
        return await collection.delete_quotation_by_id(quotation_id)
