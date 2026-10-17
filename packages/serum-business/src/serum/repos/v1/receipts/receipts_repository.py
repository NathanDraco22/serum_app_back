from typing import Any
from serum.core.counter_manager import CounterManager
from serum.tools.time_tools import TimeTools
from serum.repos.v1.common.filter_params import ReceiptFilterParams

from .data.receipts_datasource import ReceiptsDataSource
from .models.receipt_model import CreateReceipt, ReceiptInDb, UpdateReceipt


class ReceiptsRepository:
    _instance: "ReceiptsRepository|None" = None

    def __init__(self, receipts_ds: ReceiptsDataSource):
        self.receipts_ds = receipts_ds

    @classmethod
    def get_instance(cls) -> "ReceiptsRepository":
        if cls._instance is None:
            cls._instance = cls(ReceiptsDataSource())
        return cls._instance

    async def create_receipt(
        self, create_receipt: CreateReceipt, session: Any = None
    ) -> ReceiptInDb:
        receipt_number = create_receipt.receiptNumber
        if not receipt_number:
            receipt_number = await CounterManager().next_receipt_number(session)

        now = TimeTools.get_now_in_milliseconds()
        receipt_dict = create_receipt.model_dump()
        receipt_dict["receiptNumber"] = receipt_number

        new_receipt = ReceiptInDb(
            id=receipt_number,
            createdAt=now,
            updatedAt=None,
            isDeleted=False,
            **receipt_dict,
        )

        result = await self.receipts_ds.create_receipt(
            new_receipt.model_dump(), session=session
        )
        return ReceiptInDb.model_validate(result)

    async def get_all_receipts(
        self, filters: ReceiptFilterParams | None = None
    ) -> list[ReceiptInDb]:
        filters_dict = None
        if filters is not None:
            filters_dict = filters.model_dump(exclude_none=True)
        results = await self.receipts_ds.get_all_receipts(filters_dict)
        return [ReceiptInDb.model_validate(result) for result in results]

    async def get_receipt_by_id(self, receipt_id: str) -> ReceiptInDb | None:
        result = await self.receipts_ds.get_receipt_by_id(receipt_id)
        if result is None:
            return None
        return ReceiptInDb.model_validate(result)

    async def update_receipt_by_id(
        self, receipt_id: str, receipt: UpdateReceipt
    ) -> ReceiptInDb | None:
        updated_data = receipt.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.receipts_ds.update_receipt_by_id(
            receipt_id, updated_data
        )
        if result is None:
            return None
        return ReceiptInDb.model_validate(result)

    async def delete_receipt_by_id(self, receipt_id: str) -> ReceiptInDb | None:
        result = await self.receipts_ds.delete_receipt_by_id(receipt_id)
        if result is None:
            return None
        return ReceiptInDb.model_validate(result)
