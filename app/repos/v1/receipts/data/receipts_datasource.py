from typing import Any
from services.mongo_collections.v1 import ReceiptsCollection


class ReceiptsDataSource:

    async def create_receipt(
        self, receipt: dict[str, Any], session: Any = None
    ) -> dict[str, Any]:
        collection = ReceiptsCollection.get_instance()
        await collection.create_receipt(receipt, session=session)
        return receipt

    async def get_all_receipts(
        self, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        collection = ReceiptsCollection.get_instance()
        return await collection.fetch_all_receipts(filters)

    async def get_receipt_by_id(self, receipt_id: str) -> dict[str, Any] | None:
        collection = ReceiptsCollection.get_instance()
        return await collection.fetch_receipt_by_id(receipt_id)

    async def update_receipt_by_id(
        self, receipt_id: str, receipt: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ReceiptsCollection.get_instance()
        return await collection.update_receipt_by_id(receipt_id, receipt)

    async def delete_receipt_by_id(self, receipt_id: str) -> dict[str, Any] | None:
        collection = ReceiptsCollection.get_instance()
        return await collection.delete_receipt_by_id(receipt_id)
