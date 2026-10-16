from fastapi import APIRouter, Depends

from repos.v1.common.filter_params import ReceiptFilterParams
from repos.v1.receipts import ReceiptInDb, UpdateReceipt
from responses.v1 import ListResponse

from .receipts_controller import receipts_controller

receipts_router = APIRouter(tags=["receiptsV1"])


@receipts_router.get("")
async def get_all_receipts(
    query_params: ReceiptFilterParams = Depends(),
) -> ListResponse[ReceiptInDb]:
    return await receipts_controller.get_all_receipts(query_params)


@receipts_router.get("/{receipt_id}")
async def get_receipt_by_id(receipt_id: str) -> ReceiptInDb:
    return await receipts_controller.get_receipt_by_id(receipt_id)


@receipts_router.patch("/{receipt_id}")
async def update_receipt_by_id(
    receipt_id: str, body: UpdateReceipt
) -> ReceiptInDb:
    return await receipts_controller.update_receipt_by_id(receipt_id, body)

