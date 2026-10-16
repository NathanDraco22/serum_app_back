from fastapi import HTTPException, status

from repos.v1.common.filter_params import ReceiptFilterParams
from repos.v1.receipts import (
    CreateReceipt,
    ReceiptInDb,
    ReceiptsRepository,
    UpdateReceipt,
)
from responses.v1 import ListResponse


class ReceiptsController:
    def __init__(self, receipts_repo: ReceiptsRepository) -> None:
        self.receipts_repo = receipts_repo

    async def create_receipt(self, body: CreateReceipt) -> ReceiptInDb:
        return await self.receipts_repo.create_receipt(body)

    async def get_all_receipts(
        self, query_params: ReceiptFilterParams | None = None
    ) -> ListResponse[ReceiptInDb]:
        receipts = await self.receipts_repo.get_all_receipts(query_params)
        return ListResponse(count=len(receipts), data=receipts)

    async def get_receipt_by_id(self, receipt_id: str) -> ReceiptInDb:
        receipt = await self.receipts_repo.get_receipt_by_id(receipt_id)
        if receipt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found",
            )
        return receipt

    async def update_receipt_by_id(
        self, receipt_id: str, body: UpdateReceipt
    ) -> ReceiptInDb:
        updated_receipt = await self.receipts_repo.update_receipt_by_id(
            receipt_id, body
        )
        if updated_receipt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found",
            )
        return updated_receipt

    async def delete_receipt_by_id(self, receipt_id: str) -> ReceiptInDb:
        deleted_receipt = await self.receipts_repo.delete_receipt_by_id(receipt_id)
        if deleted_receipt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found",
            )
        return deleted_receipt


receipts_controller = ReceiptsController(
    receipts_repo=ReceiptsRepository.get_instance(),
)
